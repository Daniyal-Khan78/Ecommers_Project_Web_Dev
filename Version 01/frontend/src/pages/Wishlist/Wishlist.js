import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { wishlistAPI } from '../../api/wishlist';
import { useCart } from '../../context/CartContext';
import Spinner from '../../components/Spinner/Spinner';
import './Wishlist.css';

const Wishlist = () => {
  const { updateCartCount, cartCount } = useCart();

  const [items,   setItems]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy,    setBusy]    = useState(null); // item id being acted on

  const loadWishlist = useCallback(async () => {
    setLoading(true);
    try {
      const data = await wishlistAPI.getWishlist();
      if (data.success) setItems(data.data || []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadWishlist(); }, [loadWishlist]);

  const handleRemove = async (itemId) => {
    setBusy(itemId);
    try {
      const data = await wishlistAPI.removeFromWishlist(itemId);
      if (data.success) setItems(prev => prev.filter(i => i.id !== itemId));
    } finally {
      setBusy(null);
    }
  };

  const handleMoveToCart = async (itemId) => {
    setBusy(itemId);
    try {
      const data = await wishlistAPI.moveToCart(itemId);
      if (data.success) {
        setItems(prev => prev.filter(i => i.id !== itemId));
        updateCartCount(cartCount + 1);
      }
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <div className="container" style={{ padding: '4rem 0' }}><Spinner /></div>;

  return (
    <div className="wishlist-page">
      <div className="container">
        <h1>My Wishlist {items.length > 0 && <span style={{ fontSize: '1rem', color: 'var(--gray)', fontWeight: 400 }}>({items.length} items)</span>}</h1>

        {items.length === 0 ? (
          <div className="wishlist-empty">
            <div className="wishlist-empty-icon">💝</div>
            <h2>Your wishlist is empty</h2>
            <p>Save your favourite items here and come back to them anytime.</p>
            <Link to="/products" className="btn btn-primary">Explore Products</Link>
          </div>
        ) : (
          <div className="wishlist-grid">
            {items.map(item => {
              const p = item.product;
              return (
                <div className="wishlist-card" key={item.id}>
                  {p.primary_image_url ? (
                    <Link to={`/products/${p.id}`}>
                      <img src={p.primary_image_url} alt={p.name} className="wishlist-card-img" />
                    </Link>
                  ) : (
                    <div className="wishlist-img-placeholder">🛍️</div>
                  )}
                  <div className="wishlist-card-body">
                    {p.category?.name && (
                      <span className="wishlist-card-category">{p.category.name}</span>
                    )}
                    <Link to={`/products/${p.id}`} className="wishlist-card-name">{p.name}</Link>
                    <div className="wishlist-card-price">
                      <span className="wishlist-price-current">
                        ${parseFloat(p.effective_price).toFixed(2)}
                      </span>
                      {p.is_on_sale && (
                        <span className="wishlist-price-original">
                          ${parseFloat(p.price).toFixed(2)}
                        </span>
                      )}
                    </div>
                    <div className="wishlist-card-actions">
                      <button
                        className="btn btn-primary btn-move-cart"
                        onClick={() => handleMoveToCart(item.id)}
                        disabled={busy === item.id || p.stock === 0}
                      >
                        {p.stock === 0 ? 'Out of Stock' : '🛒 Move to Cart'}
                      </button>
                      <button
                        className="btn-remove-wish"
                        onClick={() => handleRemove(item.id)}
                        disabled={busy === item.id}
                        title="Remove from wishlist"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Wishlist;
