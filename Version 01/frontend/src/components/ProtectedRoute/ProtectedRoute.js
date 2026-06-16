import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

// ProtectedRoute wraps pages that require the user to be logged in.
// adminOnly=true additionally requires the user to be an admin.
//
// If the user is not authenticated:   redirect to /login
// If not admin but page is adminOnly: redirect to / (home)
// Otherwise:                          render the children normally
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, isAdmin } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    // Save the current URL so we can redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;
