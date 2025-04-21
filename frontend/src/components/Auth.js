
import React, { useState } from "react";
// import { useNavigate } from "react-router-dom";
import { auth, provider } from "../firebase";
import { signInWithPopup } from "firebase/auth";
import "./Auth.css";

const Auth = ({ setIsAuthenticated, setCurrentSection }) => {
  // Removed useNavigate in favor of manual routing
  const [email, setEmail] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState("");
  const [status, setStatus] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [lockedOut, setLockedOut] = useState(false);

  const handleLogin = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      const userEmail = result.user.email;
      setEmail(userEmail);
      await sendOtp(userEmail);
    } catch (error) {
      console.error("Login failed:", error);
      setStatus("Login failed.");
    }
  };

  const sendOtp = async (emailToSend) => {
    const res = await fetch("http://localhost:5000/send-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailToSend }),
    });

    if (res.ok) {
      setOtpSent(true);
      setStatus("OTP sent to your email.");
      setAttempts(0);
      setLockedOut(false);
    } else {
      setStatus("Failed to send OTP.");
    }
  };

  const handleVerifyOtp = async () => {
    if (lockedOut) {
      setStatus("Too many failed attempts. Please try again later.");
      return;
    }

    const res = await fetch("http://localhost:5000/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp }),
    });

    if (res.ok) {
      setIsAuthenticated(true);
      setStatus("2FA successful!");
      setCurrentSection("home"); // Redirect after success
    } else {
      const newAttempts = attempts + 1;
      setAttempts(newAttempts);
      if (newAttempts >= 3) {
        setLockedOut(true);
        setStatus("Too many failed attempts. Please try again.");
      } else {
        setStatus("Invalid or expired OTP. Attempts left: " + (3 - newAttempts));
      }
    }
  };

  return (
    <div className="auth-container">
      {!otpSent ? (
        <>
          <h2>Login to FitGPT</h2>
          <button onClick={handleLogin}>Login with Google</button>
        </>
      ) : (
        <>
          <h3>Enter OTP sent to {email}</h3>
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            placeholder="6-digit OTP"
          />
          <button onClick={handleVerifyOtp} disabled={lockedOut}>
            Verify OTP
          </button>
          <button onClick={() => sendOtp(email)} disabled={lockedOut}>
            Resend OTP
          </button>
        </>
      )}
      {status && <p>{status}</p>}
    </div>
  );
};

export default Auth;
