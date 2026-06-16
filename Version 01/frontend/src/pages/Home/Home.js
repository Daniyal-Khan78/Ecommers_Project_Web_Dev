import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { productsAPI } from '../../api/products';
import ProductCard from '../../components/ProductCard/ProductCard';
import Spinner from '../../components/Spinner/Spinner';
import './Home.css';

const Home = () => {
  const navigate = useNavigate();
  const [featured,    setFeatured]    = useState({ on_sale: [], top_rated: [], newest: [] });
  const [categories,  setCategories]  = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [featRes, catRes] = await Promise.all([
          productsAPI.getFeatured(),
          productsAPI.getCategories(),
        ]);
        if (featRes.success) setFeatured(featRes.data);
        if (catRes.success)  setCategories(catRes.data.slice(0, 6));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleHeroSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim()) navigate(`/products?q=${encodeURIComponent(searchInput.trim())}`);
  };

  if (loading) return <Spinner message="Loading ShopNest..." />;

  return (
    <div className="home">

      {/* ── Hero Section ─────────────────────────────────── */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            Shop Everything.<br />
            <span className="hero-highlight">Pay with Visa or Mastercard.</span>
          </h1>
          <p className="hero-subtitle">
            Discover thousands of products at unbeatable prices.
            Secure checkout powered by Stripe.
          </p>
          <form className="hero-search" onSubmit={handleHeroSearch}>
            <input
              type="text"
              placeholder="What are you looking for?"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="hero-search-input"
            />
            <button type="submit" className="btn btn-primary">Search</button>
          </form>
          <div className="hero-badges">
            <span>🔒 Secure Payment</span>
            <span>💳 Visa &amp; Mastercard</span>
            <span>📦 Fast Delivery</span>
            <span>↩️ Easy Returns</span>
          </div>
        </div>
        <div className="hero-image">🛍️</div>
      </section>

      {/* ── Categories ───────────────────────────────────── */}
      {categories.length > 0 && (
        <section className="section">
          <div className="container">
            <div className="section-header">
              <h2>Shop by Category</h2>
              <Link to="/products" className="see-all">See All →</Link>
            </div>
            <div className="categories-grid">
              {categories.map(cat => (
                <Link
                  key={cat.id}
                  to={`/products?category=${cat.id}`}
                  className="category-card"
                >
                  <div className="category-icon">🏷️</div>
                  <div className="category-name">{cat.name}</div>
                  <div className="category-count">{cat.product_count} items</div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── On Sale ──────────────────────────────────────── */}
      {featured.on_sale?.length > 0 && (
        <section className="section section-alt">
          <div className="container">
            <div className="section-header">
              <h2>🔥 Hot Deals</h2>
              <Link to="/products?on_sale=true" className="see-all">See All Sales →</Link>
            </div>
            <div className="grid-4">
              {featured.on_sale.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          </div>
        </section>
      )}

      {/* ── Top Rated ────────────────────────────────────── */}
      {featured.top_rated?.length > 0 && (
        <section className="section">
          <div className="container">
            <div className="section-header">
              <h2>⭐ Top Rated</h2>
              <Link to="/products?sort=rating" className="see-all">See All →</Link>
            </div>
            <div className="grid-4">
              {featured.top_rated.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          </div>
        </section>
      )}

      {/* ── Newest ───────────────────────────────────────── */}
      {featured.newest?.length > 0 && (
        <section className="section section-alt">
          <div className="container">
            <div className="section-header">
              <h2>✨ New Arrivals</h2>
              <Link to="/products?sort=newest" className="see-all">See All →</Link>
            </div>
            <div className="grid-4">
              {featured.newest.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          </div>
        </section>
      )}

      {/* ── Trust Banner ─────────────────────────────────── */}
      <section className="trust-banner">
        <div className="container">
          <div className="trust-grid">
            {[
              { icon: '🔒', title: 'Secure Payments', desc: 'Visa, Mastercard & Amex via Stripe' },
              { icon: '📦', title: 'Fast Delivery',   desc: 'Quick and reliable shipping' },
              { icon: '↩️', title: 'Easy Returns',    desc: '30-day hassle-free returns' },
              { icon: '🎧', title: '24/7 Support',    desc: 'Always here to help you' },
            ].map(item => (
              <div key={item.title} className="trust-item">
                <span className="trust-icon">{item.icon}</span>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

    </div>
  );
};

export default Home;
