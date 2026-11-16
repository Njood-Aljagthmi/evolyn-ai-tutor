import React from "react";

export function LoadingSpinner({ message = "Loading..." }) {
  return (
    <div className="spinner-overlay">
      <div className="spinner-container">
        <div className="spinner-ring"></div>
        <p className="spinner-message">{message}</p>
      </div>
    </div>
  );
}

export default LoadingSpinner;
