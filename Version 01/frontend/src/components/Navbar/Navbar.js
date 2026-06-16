import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import { authAPI } from '../../api/auth';
import { cartAPI } from '../../api/cart';
import { notificationsAPI } from '../../api/notifications';
import ThemeToggle from '../ThemeToggle/ThemeToggle';
import './Navbar.css';

const Navbar = () => {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const { cartCount, updateCartCount } = useCart();
  const navigate = useNavigate();

  const [searchQuery,    setSearchQuery]    = useState('');
  const [menuOpen,       setMenuOpen]       = useState(false);
  const [userMenuOpen,   setUserMenuOpen]   = useState(false);
  const [notifOpen,      setNotifOpen]      = useState(false);
  const [notifications,  setNotifications]  = useState([]);
  const [unreadCount,    setUnreadCount]    = useState(0);

  const notifRef = useRef(null);

  // Initialize cart count and notifications on login/refresh
  useEffect(() => {
    if (!isAuthenticated) return;

    // Cart count
    cartAPI.getCart().then(d => {
      if (d.success) updateCartCount(d.data.total_items || 0);
    }).catch(() => {});

    // Notifications unread count
    notificationsAPI.getNotifications().then(d => {
      if (d.success) {
        setNotifications(d.data.notifications || []);
        setUnreadCount(d.data.unread_count || 0);
      }
    }).catch(() => {});
  }, [isAuthenticated]); // eslint-disable-line react-hooks/exhaustive-deps

  // Close notification dropdown on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
    }
  };

  const handleLogout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    await authAPI.logout(refreshToken);
    logout();
    navigate('/');
    setUserMenuOpen(false);
  };

  const handleOpenNotif = async () => {
    setNotifOpen(!notifOpen);
    if (!notifOpen && unreadCount > 0) {
      // Mark all as read when opening
      await notificationsAPI.markAllRead().catch(() => {});
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    }
  };

  const formatNotifTime = (iso) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <nav className="navbar">
      <div className="navbar-inner">

        {/* Brand */}
        <Link to="/" className="navbar-brand">
          <span className="brand-icon">🛍️</span>
          <span className="brand-name">ShopNest</span>
        </Link>

        {/* Search */}
        <form className="navbar-search" onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            aria-label="Search products"
          />
          <button type="submit" className="search-btn" aria-label="Search">🔍</button>
        </form>

        {/* Nav links */}
        <div className={`navbar-links ${menuOpen ? 'open' : ''}`}>
          <Link to="/products" onClick={() => setMenuOpen(false)}>Products</Link>

          <ThemeToggle />

          {isAuthenticated ? (
            <>
              {/* Cart */}
              <Link to="/cart" className="cart-link" onClick={() => setMenuOpen(false)}>
                🛒
                {cartCount > 0 && (
                  <span className="cart-badge">{cartCount > 99 ? '99+' : cartCount}</span>
                )}
              </Link>

              {/* Wishlist */}
              <Link to="/wishlist" onClick={() => setMenuOpen(false)}>❤️</Link>

              {/* Notifications bell */}
              <div className="notif-wrapper" ref={notifRef}>
                <button
                  className="notif-btn"
                  onClick={handleOpenNotif}
                  aria-label="Notifications"
                >
                  🔔
                  {unreadCount > 0 && (
                    <span className="notif-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
                  )}
                </button>

                {notifOpen && (
                  <div className="notif-dropdown">
                    <div className="notif-header">
                      <span>Notifications</span>
                    </div>
                    {notifications.length === 0 ? (
                      <div className="notif-empty">No notifications yet.</div>
                    ) : (
                      <div className="notif-list">
                        {notifications.slice(0, 8).map(n => (
                          <div key={n.id} className={`notif-item ${!n.is_read ? 'unread' : ''}`}>
                            <div className="notif-title">{n.title}</div>
                            <div className="notif-msg">{n.message}</div>
                            <div className="notif-time">{formatNotifTime(n.created_at)}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* User dropdown */}
              <div className="user-menu-wrapper">
                <button
                  className="user-menu-btn"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  aria-label="User menu"
                >
                  <span className="user-avatar">
                    {user?.first_name?.[0]?.toUpperCase() || '👤'}
                  </span>
                  <span className="user-name">{user?.first_name || 'Account'}</span>
                  <span className="chevron">{userMenuOpen ? '▲' : '▼'}</span>
                </button>

                {userMenuOpen && (
                  <div className="user-dropdown">
                    <Link to="/profile"  onClick={() => setUserMenuOpen(false)}>👤 My Profile</Link>
                    <Link to="/orders"   onClick={() => setUserMenuOpen(false)}>📦 My Orders</Link>
                    <Link to="/wishlist" onClick={() => setUserMenuOpen(false)}>❤️ Wishlist</Link>
                    {isAdmin && (
                      <>
                        <div className="dropdown-divider" />
                        <Link to="/admin" onClick={() => setUserMenuOpen(false)}>⚙️ Admin Dashboard</Link>
                      </>
                    )}
                    <div className="dropdown-divider" />
                    <button onClick={handleLogout} className="logout-btn">🚪 Logout</button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login"    className="btn btn-secondary nav-auth-btn" onClick={() => setMenuOpen(false)}>Login</Link>
              <Link to="/register" className="btn btn-primary  nav-auth-btn" onClick={() => setMenuOpen(false)}>Sign Up</Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="hamburger"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          {menuOpen ? '✕' : '☰'}
        </button>

      </div>
    </nav>
  );
};

export default Navbar;
