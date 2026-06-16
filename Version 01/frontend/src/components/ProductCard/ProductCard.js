import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import { cartAPI } from '../../api/cart';
import { wishlistAPI } from '../../api/wishlist';
import './ProductCard.css';

const ProductCard = ({ product }) => {
  const { isAuthenticated } = useAuth();
  const { updateCartCount, cartCount } = useCart();
  const navigate = useNavigate();

  const [addingToCart,     setAddingToCart]     = useState(false);
  const [wishlisted,       setWishlisted]       = useState(false);
  const [wishlistItemId,   setWishlistItemId]   = useState(null);
  const [cartMsg,          setCartMsg]          = useState('');

  const {
    id, name, price, effective_price,
    discount_percent, is_on_sale, primary_image_url,
    category, rating, rating_count, stock,
  } = product;

  // ── Add to Cart ───────────────────────────────────────
  const handleAddToCart = async (e) => {
    e.preventDefault(); // Don't navigate to product page
    if (!isAuthenticated) { navigate('/login'); return; }
    if (stock === 0) return;

    setAddingToCart(true);
    setCartMsg('');
    try {
      const data = await cartAPI.addToCart(id, 1);
      if (data.success) {
        updateCartCount(cartCount + 1);
        setCartMsg('Added!');
        setTimeout(() => setCartMsg(''), 2000);
      }
    } catch {
      setCartMsg('Error');
    }
    setAddingToCart(false);
  };

  // ── Toggle Wishlist ───────────────────────────────────
  const handleWishlist = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) { navigate('/login'); return; }

    try {
      if (wishlisted && wishlistItemId) {
        await wishlistAPI.removeFromWishlist(wishlistItemId);
        setWishlisted(false);
        setWishlistItemId(null);
      } else {
        const data = await wishlistAPI.addToWishlist(id);
        if (data.success) {
          setWishlisted(true);
          setWishlistItemId(data.data?.item?.id);
        }
      }
    } catch {
      // Silent fail — wishlist is not critical
    }
  };

  // ── Render star rating ────────────────────────────────
  const renderStars = (r) => {
    const full  = Math.floor(r);
    const half  = r - full >= 0.5;
    const empty = 5 - full - (half ? 1 : 0);
    return (
      '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty)
    );
  };

  return (
    <Link to={`/products/${id}`} className="product-card">
      {/* Sale badge */}
      {is_on_sale && (
        <span className="sale-badge">-{discount_percent}%</span>
      )}

      {/* Wishlist button */}
      <button
        className={`wishlist-btn ${wishlisted ? 'active' : ''}`}
        onClick={handleWishlist}
        aria-label={wishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
      >
        {wishlisted ? '❤️' : '🤍'}
      </button>

      {/* Product Image */}
      <div className="product-image-wrap">
        {primary_image_url ? (
          <img src={primary_image_url} alt={name} className="product-image" loading="lazy" />
        ) : (
          <div className="product-image-placeholder">🛍️</div>
        )}
        {stock === 0 && <div className="out-of-stock-overlay">Out of Stock</div>}
      </div>

      {/* Info */}
      <div className="product-info">
        {category?.name && (
          <span className="product-category">{category.name}</span>
        )}

        <h3 className="product-name">{name}</h3>

        {/* Rating */}
        {rating_count > 0 && (
          <div className="product-rating">
            <span className="stars">{renderStars(parseFloat(rating))}</span>
            <span className="rating-count">({rating_count})</span>
          </div>
        )}

        {/* Price */}
        <div className="product-price">
          <span className="price-current">${parseFloat(effective_price).toFixed(2)}</span>
          {is_on_sale && (
            <span className="price-original">${parseFloat(price).toFixed(2)}</span>
          )}
        </div>

        {/* Add to Cart */}
        <button
          className={`btn btn-primary add-to-cart-btn ${addingToCart ? 'loading' : ''} ${cartMsg === 'Added!' ? 'success' : ''}`}
          onClick={handleAddToCart}
          disabled={addingToCart || stock === 0}
        >
          {stock === 0 ? 'Out of Stock' : cartMsg || (addingToCart ? 'Adding...' : '🛒 Add to Cart')}
        </button>
      </div>
    </Link>
  );
};

export default ProductCard;
