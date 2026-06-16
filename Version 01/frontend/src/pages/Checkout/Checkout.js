import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { cartAPI } from '../../api/cart';
import { ordersAPI } from '../../api/orders';
import { paymentsAPI } from '../../api/payments';
import { useCart } from '../../context/CartContext';
import Spinner from '../../components/Spinner/Spinner';
import './Checkout.css';

/* ── Stripe card form (must be inside <Elements>) ─────────────────── */
const CardPaymentForm = ({ clientSecret, orderId, total, onSuccess, onError }) => {
  const stripe   = useStripe();
  const elements = useElements();
  const [paying,   setPaying]   = useState(false);
  const [cardError, setCardError] = useState('');

  const handlePay = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    setPaying(true);
    setCardError('');

    const cardEl = elements.getElement(CardElement);
    const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
      payment_method: { card: cardEl },
    });

    if (error) {
      setCardError(error.message || 'Payment failed. Please try again.');
      setPaying(false);
      return;
    }

    if (paymentIntent.status === 'succeeded') {
      const res = await paymentsAPI.confirmPayment(orderId, paymentIntent.id);
      if (res.success) {
        onSuccess(orderId);
      } else {
        onError(res.message || 'Could not confirm payment with server.');
      }
    } else {
      onError('Payment was not completed. Please try again.');
    }
    setPaying(false);
  };

  return (
    <form onSubmit={handlePay}>
      <div className="stripe-card-section">
        <h3>Card Details</h3>
        <div className="card-element-wrap">
          <CardElement options={{ style: { base: { fontSize: '16px', color: '#1e293b' } } }} />
        </div>
        <div className="accepted-cards">
          <span>Accepted:</span>
          {['Visa', 'Mastercard', 'Amex'].map(c => (
            <span key={c} className="card-brand-badge">{c}</span>
          ))}
        </div>
      </div>
      {cardError && <div className="checkout-error">{cardError}</div>}
      <button type="submit" className="btn btn-primary btn-place-order" disabled={paying || !stripe}>
        {paying ? 'Processing...' : `Pay $${total ? total.toFixed(2) : ''}`}
      </button>
    </form>
  );
};

/* ── Main Checkout component ─────────────────────────────────────── */
const Checkout = () => {
  const navigate = useNavigate();
  const { clearCartCount } = useCart();

  const [cart,           setCart]           = useState(null);
  const [loadingCart,    setLoadingCart]     = useState(true);
  const [step,           setStep]           = useState('form');  // 'form' | 'pay'
  const [placing,        setPlacing]        = useState(false);
  const [error,          setError]          = useState('');

  // Form state
  const [shippingAddress, setShippingAddress] = useState('');
  const [paymentMethod,   setPaymentMethod]   = useState('cod');
  const [notes,           setNotes]           = useState('');

  // Payment step state
  const [stripePromise,  setStripePromise]  = useState(null);
  const [clientSecret,   setClientSecret]   = useState('');
  const [currentOrderId, setCurrentOrderId] = useState(null);

  const loadCart = useCallback(async () => {
    setLoadingCart(true);
    try {
      const data = await cartAPI.getCart();
      if (data.success) setCart(data.data);
    } finally {
      setLoadingCart(false);
    }
  }, []);

  useEffect(() => { loadCart(); }, [loadCart]);

  const handlePlaceOrder = async (e) => {
    e.preventDefault();
    setError('');
    setPlacing(true);

    const orderData = await ordersAPI.placeOrder({
      shipping_address: shippingAddress,
      payment_method:   paymentMethod,
      notes,
    });

    if (!orderData.success) {
      setError(orderData.message || 'Could not place order. Please try again.');
      setPlacing(false);
      return;
    }

    const orderId = orderData.data.id;
    setCurrentOrderId(orderId);

    if (paymentMethod === 'cod') {
      clearCartCount();
      navigate(`/orders/${orderId}`);
      return;
    }

    // Stripe: create payment intent
    const intentData = await paymentsAPI.createIntent(orderId);
    if (!intentData.success) {
      setError(intentData.message || 'Could not create payment session.');
      setPlacing(false);
      return;
    }

    setClientSecret(intentData.data.client_secret);
    setStripePromise(loadStripe(intentData.data.publishable_key));
    setStep('pay');
    setPlacing(false);
  };

  const handlePaymentSuccess = (orderId) => {
    clearCartCount();
    navigate(`/orders/${orderId}`);
  };

  const handlePaymentError = (msg) => {
    setError(msg);
    setStep('form');
  };

  if (loadingCart) return <div className="container" style={{ padding: '4rem 0' }}><Spinner /></div>;

  const items   = cart?.items || [];
  const total   = parseFloat(cart?.total_price || 0);
  const savings = parseFloat(cart?.savings || 0);

  if (items.length === 0) {
    return (
      <div className="checkout-page">
        <div className="container" style={{ textAlign: 'center', padding: '5rem 0' }}>
          <h2>Your cart is empty</h2>
          <p style={{ color: 'var(--gray)', margin: '0.75rem 0 1.5rem' }}>Add items before checking out.</p>
          <a href="/products" className="btn btn-primary">Shop Now</a>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <div className="container">
        <h1>Checkout</h1>

        {/* Step indicator */}
        <div className="checkout-steps">
          <div className={`checkout-step-indicator ${step === 'form' ? 'active' : 'done'}`}>
            <span className="step-num">{step === 'pay' ? '✓' : '1'}</span>
            Shipping
          </div>
          <div className="step-sep" />
          <div className={`checkout-step-indicator ${step === 'pay' ? 'active' : ''}`}>
            <span className="step-num">2</span>
            Payment
          </div>
        </div>

        <div className="checkout-layout">

          {/* Left: form / payment */}
          <div>
            {step === 'form' && (
              <div className="checkout-form-card">
                <h2>Shipping & Payment</h2>
                <form onSubmit={handlePlaceOrder}>

                  <div className="form-group">
                    <label className="form-label">Shipping Address *</label>
                    <textarea
                      className="form-control"
                      rows={3}
                      placeholder="Street, City, State, ZIP"
                      value={shippingAddress}
                      onChange={e => setShippingAddress(e.target.value)}
                      required
                      minLength={10}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Notes (optional)</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Leave at door, etc."
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Payment Method</label>
                    <div className="payment-methods">
                      <button
                        type="button"
                        className={`payment-method-option ${paymentMethod === 'stripe' ? 'selected' : ''}`}
                        onClick={() => setPaymentMethod('stripe')}
                      >
                        <span className="payment-method-icon">💳</span>
                        <span className="payment-method-label">Credit / Debit Card</span>
                        <span className="payment-method-sub">Visa · Mastercard · Amex</span>
                      </button>
                      <button
                        type="button"
                        className={`payment-method-option ${paymentMethod === 'cod' ? 'selected' : ''}`}
                        onClick={() => setPaymentMethod('cod')}
                      >
                        <span className="payment-method-icon">💵</span>
                        <span className="payment-method-label">Cash on Delivery</span>
                        <span className="payment-method-sub">Pay when you receive</span>
                      </button>
                    </div>
                  </div>

                  {error && <div className="checkout-error">{error}</div>}

                  <button type="submit" className="btn btn-primary btn-place-order" disabled={placing}>
                    {placing ? 'Placing Order...' : (paymentMethod === 'cod' ? 'Place Order' : 'Continue to Payment')}
                  </button>
                </form>
              </div>
            )}

            {step === 'pay' && stripePromise && (
              <div className="checkout-form-card">
                <h2>Complete Payment</h2>
                <p style={{ color: 'var(--gray)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                  Order #{currentOrderId} · Total: <strong>${total.toFixed(2)}</strong>
                </p>
                <Elements stripe={stripePromise}>
                  <CardPaymentForm
                    clientSecret={clientSecret}
                    orderId={currentOrderId}
                    total={total}
                    onSuccess={handlePaymentSuccess}
                    onError={handlePaymentError}
                  />
                </Elements>
                {error && <div className="checkout-error">{error}</div>}
              </div>
            )}
          </div>

          {/* Right: order summary */}
          <div className="checkout-summary">
            <h2>Order Summary</h2>

            <div className="checkout-summary-items">
              {items.map(item => (
                <div className="checkout-summary-item" key={item.id}>
                  {item.product.primary_image_url ? (
                    <img src={item.product.primary_image_url} alt={item.product.name} className="checkout-summary-img" />
                  ) : (
                    <div className="checkout-summary-img" style={{ background: 'var(--light-gray)', display:'flex', alignItems:'center', justifyContent:'center' }}>🛍️</div>
                  )}
                  <div style={{ flex: 1 }}>
                    <div className="checkout-summary-name">{item.product.name}</div>
                    <div className="checkout-summary-qty">×{item.quantity}</div>
                  </div>
                  <span className="checkout-summary-subtotal">${parseFloat(item.subtotal).toFixed(2)}</span>
                </div>
              ))}
            </div>

            <div className="summary-row" style={{ display:'flex', justifyContent:'space-between', padding:'0.5rem 0', fontSize:'0.95rem', color:'var(--gray)' }}>
              <span>Subtotal</span>
              <span>${(total + savings).toFixed(2)}</span>
            </div>
            {savings > 0 && (
              <div className="summary-row" style={{ display:'flex', justifyContent:'space-between', padding:'0.4rem 0', fontSize:'0.95rem', color:'var(--success)' }}>
                <span>Savings</span>
                <span>−${savings.toFixed(2)}</span>
              </div>
            )}
            <div style={{ display:'flex', justifyContent:'space-between', padding:'0.75rem 0', marginTop:'0.5rem', borderTop:'2px solid var(--dark)', fontWeight:700, fontSize:'1.1rem' }}>
              <span>Total</span>
              <span>${total.toFixed(2)}</span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Checkout;
