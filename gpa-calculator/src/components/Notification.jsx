import React, { useEffect, useState } from 'react';

const Notification = ({ message, type, onClose }) => {
  const [show, setShow] = useState(false);

  useEffect(() => {
    // Trigger animation
    setTimeout(() => setShow(true), 10);

    // Auto-close after 3 seconds
    const timer = setTimeout(() => {
      setShow(false);
      setTimeout(onClose, 300);
    }, 3000);

    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`notification notification-${type} ${show ? 'show' : ''}`}>
      {message}
    </div>
  );
};

export default Notification;