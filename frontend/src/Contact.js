import React, { useState } from 'react';
import './Contact.css';

const Contact = () => {
  const [email, setEmail] = useState('');
  const [topic, setTopic] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`Thank you for contacting us! We'll get back to you at ${email}.`);
    setEmail('');
    setTopic('');
    setMessage('');
  };

  return (
    <div className="contact-container">
      <h1>Contact Us</h1>
      <p className="contact-intro">
        Already use FitGPT? <a href="/signin">Sign in</a> so we can tailor your support experience.
        If that’s not possible, we’d still like to hear from you.
      </p>

      <form onSubmit={handleSubmit} className="contact-form">
        <div className="form-group">
          <label htmlFor="email">Your Email Address</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="topic">Select a topic:</label>
          <select
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            required
          >
            <option value="" disabled>Choose a topic</option>
            <option value="audio-video">Audio & Video</option>
            <option value="billing-plans">Billing & Plans</option>
            <option value="connection-trouble">Connection Trouble</option>
            <option value="managing-channels">Managing Channels</option>
            <option value="managing-members">Managing Members</option>
            <option value="notifications">Notifications</option>
            <option value="signing-in">Signing In</option>
            <option value="slack-connect">FitGPT Connect</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="message">Or tell us what you need help with:</label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter a topic, like 'notifications'"
            required
          />
        </div>

        <button type="submit" className="submit-button">
          Get Help
        </button>
      </form>

      <p className="privacy-policy">
        By submitting this form, you agree to our <a href="/privacy-policy">Privacy Policy</a>.
      </p>
    </div>
  );
};

export default Contact;