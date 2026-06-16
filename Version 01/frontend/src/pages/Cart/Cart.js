import React, { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { cartAPI } from '../../api/cart';
import { useCart } from '../../context/CartContext';
import Spinner from '../../components/Spinner/Spinner';
import './Cart.css';

const Cart = () => {
  const navigate = useNavigate();
  const { updateCartCount } = useCart();

  const [cart,     setCart]     = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [updating, setUpdating] = useState(null); // item id being updated

  const loadCart = useCallback(async () => {
    setLoading(true);
    try {
      const data = await cartAPI.getCart();
      if (data.success) {
        setCart(data.data);
        updateCartCount(data.data.total_items || 0);
      }
    } finally {
      setLoading(false);
    }
  }, [updateCartCount]);

  useEffect(() => { loadCart(); }, [loadCart]);

  const handleUpdateQty = async (itemId, newQty) => {
    setUpdating(itemId);
    try {
      const data = await cartAPI.updateItem(itemId, newQty);
      if (data.success) {
        setCart(data.data);
        updateCartCount(data.data.total_items || 0);
      }
    } finally {
      setUpdating(null);
    }
  };

  const handleRemove = async (itemId) => {
    setUpdating(itemId);
    try {
      const data = await cartAPI.removeItem(itemId);
      if (data.success) {
        setCart(data.data);
        updateCartCount(data.data.total_items || 0);
      }
    } finally {
      setUpdating(null);
    }
  };

  const handleClear = async () => {
    if (!window.confirm('Remove all items from your cart?')) return;
    const data = await cartAPI.clearCart();
    if (data.success) {
      setCart(data.data);
      updateCartCount(0);
    }
  };

  if (loading) return <div className="container" style={{ padding: '4rem 0' }}><Spinner /></div>;

  const items = cart?.items || [];
  const isEmpty = items.length === 0;

  if (isEmpty) {
    return (
      <div className="cart-page">
        <div className="container">
          <h1>Shopping Cart</h1>
          <div className="cart-empty">
            <div className="cart-empty-icon">🛒</div>
            <h2>Your cart is empty</h2>
            <p>Looks like you haven't added anything yet.</p>
            <Link to="/products" className="btn btn-primary">Start Shopping</Link>
          </div>
        </div>
      </div>
    );
  }

  const subtotal = parseFloat(cart.total_price || 0);
  const savings  = parseFloat(cart.savings || 0);

  return (
    <div className="cart-page">
      <div className="container">
        <h1>Shopping Cart ({cart.total_items} item{cart.total_items !== 1 ? 's' : ''})</h1>

        <div className="cart-layout">

          {/* Items list */}
          <div className="cart-items">
            {items.map(item => {
              const p = item.product;
              const busy = updating === item.id;
              return (
                <div className="cart-item" key={item.id}>

                  {/* Image */}
                  <div className="cart-item-image">
                    {p.primary_image_url ? (
                      <img src={p.primary_image_url} alt={p.name} />
                    ) : (
                      <span className="cart-item-image-placeholder">🛍️</span>
                    )}
                  </div>

                  {/* Info */}
                  <div className="cart-item-info">
                    <Link to={`/products/${p.id}`} className="cart-item-name">{p.name}</Link>
                    {p.category?.name && (
                      <span className="cart-item-category">{p.category.name}</span>
                    )}
                    <span className="cart-item-unit-price">
                      ${parseFloat(p.effective_price).toFixed(2)} each
                    </span>
                    <span className="cart-item-subtotal">
                      ${parseFloat(item.subtotal).toFixed(2)}
                    </span>
                  </div>

                  {/* Qty + remove */}
                  <div className="cart-item-actions">
                    <div className="cart-qty-control">
                      <button
                        className="cart-qty-btn"
                        onClick={() => handleUpdateQty(item.id, item.quantity - 1)}
                        disabled={busy || item.quantity <= 1}
                      >−</button>
                      <span className="cart-qty-value">{item.quantity}</span>
                      <button
                        className="cart-qty-btn"
                        onClick={() => handleUpdateQty(item.id, item.quantity + 1)}
                        disabled={busy || item.quantity >= p.stock}
                      >+</button>
                    </div>
                    <button
                      className="cart-remove-btn"
                      onClick={() => handleRemove(item.id)}
                      disabled={busy}
                    >
                      Remove
                    </button>
                  </div>

                </div>
              );
            })}

            {items.length > 1 && (
              <div style={{ textAlign: 'right' }}>
                <button className="cart-remove-btn" onClick={handleClear}>
                  Clear entire cart
                </button>
              </div>
            )}
          </div>

          {/* Order summary sidebar */}
          <div className="order-summary">
            <h2>Order Summary</h2>

            <div className="summary-row">
              <span>Subtotal ({cart.total_items} items)</span>
              <span>${(subtotal + savings).toFixed(2)}</span>
            </div>

            {savings > 0 && (
              <div className="summary-row savings">
                <span>Discount savings</span>
                <span>−${savings.toFixed(2)}</span>
              </div>
            )}

            <div className="summary-total">
              <span>Total</span>
              <span>${subtotal.toFixed(2)}</span>
            </div>

            <button
              className="btn btn-primary btn-checkout"
              onClick={() => navigate('/checkout')}
            >
              Proceed to Checkout
            </button>

            <Link to="/products" className="btn-continue">← Continue Shopping</Link>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Cart;
