import React from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

const Footer = () => (
  <footer className="footer">
    <div className="container">
      <div className="footer-grid">
        <div className="footer-brand">
          <div className="footer-logo">🛍️ ShopNest</div>
          <p>Your one-stop online shopping destination. Quality products, great prices, fast delivery.</p>
        </div>

        <div className="footer-links">
          <h4>Shop</h4>
          <Link to="/products">All Products</Link>
          <Link to="/products?on_sale=true">Sale</Link>
          <Link to="/products?sort=newest">New Arrivals</Link>
          <Link to="/products?sort=rating">Top Rated</Link>
        </div>

        <div className="footer-links">
          <h4>Account</h4>
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
          <Link to="/orders">My Orders</Link>
          <Link to="/wishlist">Wishlist</Link>
        </div>

        <div className="footer-links">
          <h4>Support</h4>
          <span>💳 Visa &amp; Mastercard accepted</span>
          <span>🔒 Secure Checkout (Stripe)</span>
          <span>📦 Fast Delivery</span>
          <span>↩️ Easy Returns</span>
        </div>
      </div>

      <div className="footer-bottom">
        <p>© {new Date().getFullYear()} ShopNest. All rights reserved.</p>
        <div className="payment-badges">
          <span>VISA</span>
          <span>Mastercard</span>
          <span>Amex</span>
          <span>🔒 Secured by Stripe</span>
        </div>
      </div>
    </div>
  </footer>
);

export default Footer;
