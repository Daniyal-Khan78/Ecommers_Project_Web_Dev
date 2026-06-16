import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { productsAPI } from '../../api/products';
import { cartAPI } from '../../api/cart';
import { wishlistAPI } from '../../api/wishlist';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import ProductCard from '../../components/ProductCard/ProductCard';
import Spinner from '../../components/Spinner/Spinner';
import './ProductDetail.css';

const renderStars = (r) => {
  const val  = parseFloat(r) || 0;
  const full = Math.floor(val);
  const half = val - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty);
};

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { updateCartCount, cartCount } = useCart();

  const [product,        setProduct]        = useState(null);
  const [related,        setRelated]        = useState([]);
  const [loading,        setLoading]        = useState(true);
  const [error,          setError]          = useState('');
  const [activeImage,    setActiveImage]    = useState(null);
  const [quantity,       setQuantity]       = useState(1);
  const [wishlisted,     setWishlisted]     = useState(false);
  const [wishlistItemId, setWishlistItemId] = useState(null);
  const [addingToCart,   setAddingToCart]   = useState(false);
  const [cartMsg,        setCartMsg]        = useState('');

  // Load product
  const loadProduct = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await productsAPI.getProduct(id);
      if (data.success) {
        setProduct(data.data);
        setActiveImage(data.data.primary_image_url);
        setQuantity(1);
      } else {
        setError('Product not found.');
      }
    } catch {
      setError('Failed to load product.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadProduct(); }, [loadProduct]);

  // Load related products (same category, exclude self)
  useEffect(() => {
    if (!product?.category?.id) return;
    productsAPI.getProducts({ category: product.category.id, page: 1 }).then(d => {
      if (d.success) {
        const filtered = (d.data || []).filter(p => p.id !== product.id).slice(0, 4);
        setRelated(filtered);
      }
    });
  }, [product]);

  // Check wishlist status on load
  useEffect(() => {
    if (!isAuthenticated || !product) return;
    wishlistAPI.checkWishlist(product.id).then(d => {
      if (d.success && d.data) {
        setWishlisted(d.data.is_wishlisted);
        setWishlistItemId(d.data.wishlist_item_id || null);
      }
    }).catch(() => {});
  }, [isAuthenticated, product]);

  const handleAddToCart = async () => {
    if (!isAuthenticated) { navigate('/login'); return; }
    if (!product || product.stock === 0) return;

    setAddingToCart(true);
    setCartMsg('');
    try {
      const data = await cartAPI.addToCart(product.id, quantity);
      if (data.success) {
        updateCartCount(cartCount + quantity);
        setCartMsg('Added to cart!');
        setTimeout(() => setCartMsg(''), 3000);
      } else {
        setCartMsg(data.message || 'Could not add to cart.');
        setTimeout(() => setCartMsg(''), 3000);
      }
    } catch {
      setCartMsg('Error adding to cart.');
      setTimeout(() => setCartMsg(''), 3000);
    } finally {
      setAddingToCart(false);
    }
  };

  const handleWishlist = async () => {
    if (!isAuthenticated) { navigate('/login'); return; }
    try {
      if (wishlisted && wishlistItemId) {
        await wishlistAPI.removeFromWishlist(wishlistItemId);
        setWishlisted(false);
        setWishlistItemId(null);
      } else {
        const data = await wishlistAPI.addToWishlist(product.id);
        if (data.success) {
          setWishlisted(true);
          setWishlistItemId(data.data?.item?.id || null);
        }
      }
    } catch {
      // silent fail
    }
  };

  const stockStatus = () => {
    if (!product) return null;
    if (product.stock === 0) return <span className="product-detail-stock stock-out">Out of Stock</span>;
    if (product.stock <= 5)  return <span className="product-detail-stock stock-low">Only {product.stock} left</span>;
    return <span className="product-detail-stock stock-in">In Stock</span>;
  };

  if (loading) return <div className="container" style={{ padding: '4rem 0' }}><Spinner /></div>;
  if (error)   return (
    <div className="container" style={{ padding: '4rem 0', textAlign: 'center' }}>
      <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error}</p>
      <Link to="/products" className="btn btn-primary">Back to Products</Link>
    </div>
  );
  if (!product) return null;

  const images = product.images || [];

  return (
    <div className="product-detail-page">
      <div className="container">

        {/* Breadcrumb */}
        <nav className="breadcrumb">
          <Link to="/">Home</Link>
          <span className="breadcrumb-sep">›</span>
          <Link to="/products">Products</Link>
          {product.category && (
            <>
              <span className="breadcrumb-sep">›</span>
              <Link to={`/products?category=${product.category.id}`}>{product.category.name}</Link>
            </>
          )}
          <span className="breadcrumb-sep">›</span>
          <span>{product.name}</span>
        </nav>

        {/* Main grid */}
        <div className="product-detail-grid">

          {/* Gallery */}
          <div className="product-gallery">
            <div className="gallery-main">
              {activeImage ? (
                <img src={activeImage} alt={product.name} />
              ) : (
                <span className="gallery-placeholder">🛍️</span>
              )}
            </div>

            {images.length > 1 && (
              <div className="gallery-thumbs">
                {images.map(img => (
                  <button
                    key={img.id}
                    className={`gallery-thumb ${activeImage === img.image_url ? 'active' : ''}`}
                    onClick={() => setActiveImage(img.image_url)}
                    aria-label={img.alt_text || 'Product image'}
                  >
                    <img src={img.image_url} alt={img.alt_text || product.name} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Info panel */}
          <div className="product-info-panel">

            {product.category && (
              <Link
                to={`/products?category=${product.category.id}`}
                className="product-detail-category"
              >
                {product.category.name}
              </Link>
            )}

            <h1 className="product-detail-name">{product.name}</h1>

            {/* Rating */}
            {product.rating_count > 0 && (
              <div className="product-detail-rating">
                <span className="detail-stars">{renderStars(product.rating)}</span>
                <span className="detail-rating-value">{parseFloat(product.rating).toFixed(1)}</span>
                <span className="detail-rating-count">({product.rating_count} reviews)</span>
              </div>
            )}

            {/* Price */}
            <div className="product-detail-price">
              <span className="detail-price-current">
                ${parseFloat(product.effective_price).toFixed(2)}
              </span>
              {product.is_on_sale && (
                <>
                  <span className="detail-price-original">
                    ${parseFloat(product.price).toFixed(2)}
                  </span>
                  <span className="detail-sale-badge">-{product.discount_percent}%</span>
                </>
              )}
            </div>

            {/* Stock status */}
            {stockStatus()}

            {/* Quantity + actions */}
            <div className="product-actions">
              {product.stock > 0 && (
                <div className="quantity-row">
                  <span className="qty-label">Qty:</span>
                  <div className="qty-control">
                    <button
                      className="qty-btn"
                      onClick={() => setQuantity(q => Math.max(1, q - 1))}
                      disabled={quantity <= 1}
                    >−</button>
                    <span className="qty-value">{quantity}</span>
                    <button
                      className="qty-btn"
                      onClick={() => setQuantity(q => Math.min(product.stock, q + 1))}
                      disabled={quantity >= product.stock}
                    >+</button>
                  </div>
                </div>
              )}

              <div className="action-row">
                <button
                  className="btn btn-primary btn-add-cart"
                  onClick={handleAddToCart}
                  disabled={addingToCart || product.stock === 0}
                >
                  {product.stock === 0
                    ? 'Out of Stock'
                    : addingToCart
                    ? 'Adding...'
                    : '🛒 Add to Cart'}
                </button>

                <button
                  className={`btn-wishlist ${wishlisted ? 'active' : ''}`}
                  onClick={handleWishlist}
                  title={wishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
                >
                  {wishlisted ? '❤️' : '🤍'}
                </button>
              </div>

              {cartMsg && <p className="cart-feedback">{cartMsg}</p>}
            </div>

            {/* Description */}
            {product.description && (
              <div className="product-description">
                <h3>Description</h3>
                <p>{product.description}</p>
              </div>
            )}

          </div>
        </div>

        {/* Related products */}
        {related.length > 0 && (
          <section className="related-products">
            <h2>Related Products</h2>
            <div className="related-grid">
              {related.map(p => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          </section>
        )}

      </div>
    </div>
  );
};

export default ProductDetail;
