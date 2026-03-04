import React from 'react';

const Header = () => {
  return (
    <header className="header">
      <div className="container">
        <h1 className="logo">GPA Calculator</h1>
        <nav className="nav">
          <ul className="nav-list">
            <li><a href="#calculator">Calculator</a></li>
            <li><a href="#how-it-works">How It Works</a></li>
            <li><a href="#about">About</a></li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;