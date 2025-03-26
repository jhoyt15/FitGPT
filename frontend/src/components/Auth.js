import React, { useState, useRef, useEffect } from 'react';
import { 
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signOut,
    GoogleAuthProvider,
    signInWithPopup,
    sendPasswordResetEmail,
    sendEmailVerification,
    deleteUser
} from 'firebase/auth';
import { auth } from '../firebase';
import './Auth.css';

const Auth = ({ onLogin, onLogout, user }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [isForgotPassword, setIsForgotPassword] = useState(false);
    const [passwordError, setPasswordError] = useState('');
    const [passwordStrength, setPasswordStrength] = useState('');
    const [passwordCriteria, setPasswordCriteria] = useState({
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        special: false
    });
    const [verificationSent, setVerificationSent] = useState(false);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
    const [deleteError, setDeleteError] = useState('');
    const menuRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setShowUserMenu(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const syncUserWithBackend = async (firebaseUser) => {
        try {
            const response = await fetch('http://localhost:5000/auth/google', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: await firebaseUser.getIdToken(),
                    email: firebaseUser.email,
                    name: firebaseUser.displayName,
                    profile_pic: firebaseUser.photoURL
                }),
                credentials: 'include'
            });

            const data = await response.json();
            if (data.status === 'success' && data.user) {
                onLogin(data.user);
            } else {
                throw new Error('Failed to sync user with backend');
            }
        } catch (error) {
            console.error('Error syncing user with backend:', error);
            throw error;
        }
    };

    const checkPasswordStrength = (password) => {
        const criteria = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };
        
        setPasswordCriteria(criteria);
        
        // Calculate strength based on how many criteria are met
        const strengthScore = Object.values(criteria).filter(Boolean).length;
        
        if (strengthScore < 3) {
            setPasswordStrength('weak');
            return false;
        } else if (strengthScore < 5) {
            setPasswordStrength('medium');
            return true;
        } else {
            setPasswordStrength('strong');
            return true;
        }
    };

    const handleFirebaseLogin = async (e) => {
        e.preventDefault();
        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            
            // Check if email is verified
            if (!userCredential.user.emailVerified) {
                setError('Please verify your email before logging in. Check your inbox for the verification link.');
                // Optionally, add a button to resend verification email
                return;
            }

            await syncUserWithBackend(userCredential.user);
        } catch (error) {
            setError(error.message);
        }
    };

    const handleFirebaseRegister = async (e) => {
        e.preventDefault();
        
        try {
            // Create the user account
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            
            // Send verification email
            await sendEmailVerification(userCredential.user);
            
            setVerificationSent(true);
            setError('');
            
            // Show verification message instead of automatically logging in
            setSuccessMessage('Verification email sent! Please check your inbox and verify your email before logging in.');
            
        } catch (error) {
            setError(error.message);
            setVerificationSent(false);
        }
    };

    const handleGoogleLogin = async () => {
        try {
            const provider = new GoogleAuthProvider();
            const result = await signInWithPopup(auth, provider);
            
            // Get the token and user info
            const token = await result.user.getIdToken();
            const email = result.user.email;
            const name = result.user.displayName;
            const profile_pic = result.user.photoURL;
            const uid = result.user.uid;
            
            console.log("Firebase token obtained successfully");
            
            // Create user data from Firebase
            const userData = {
                id: uid,
                email,
                name,
                profile_pic
            };
            
            // Log the user in immediately using Firebase data
            onLogin(userData);
            
            // Then silently sync with backend
            const silentSync = () => {
                try {
                    // Generate unique IDs for our elements
                    const iframeId = `silent-iframe-${Date.now()}`;
                    const formId = `silent-form-${Date.now()}`;
                    
                    // Create a hidden form that will submit via POST without triggering CORS errors
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = 'http://localhost:5000/auth/google';
                    form.target = iframeId;
                    form.style.display = 'none';
                    form.id = formId;
                    
                    // Add token as hidden field
                    const tokenField = document.createElement('input');
                    tokenField.type = 'hidden';
                    tokenField.name = 'token';
                    tokenField.value = token;
                    form.appendChild(tokenField);
                    
                    // Add other fields
                    const emailField = document.createElement('input');
                    emailField.type = 'hidden';
                    emailField.name = 'email';
                    emailField.value = email;
                    form.appendChild(emailField);
                    
                    const nameField = document.createElement('input');
                    nameField.type = 'hidden';
                    nameField.name = 'name';
                    nameField.value = name;
                    form.appendChild(nameField);
                    
                    const picField = document.createElement('input');
                    picField.type = 'hidden';
                    picField.name = 'profile_pic';
                    picField.value = profile_pic || '';
                    form.appendChild(picField);
                    
                    // Create hidden iframe to receive the response
                    const iframe = document.createElement('iframe');
                    iframe.name = iframeId;
                    iframe.id = iframeId;
                    iframe.style.display = 'none';
                    
                    // Safe cleanup function
                    const cleanupElements = () => {
                        setTimeout(() => {
                            try {
                                const frameElement = document.getElementById(iframeId);
                                const formElement = document.getElementById(formId);
                                
                                if (frameElement && frameElement.parentNode) {
                                    frameElement.parentNode.removeChild(frameElement);
                                }
                                
                                if (formElement && formElement.parentNode) {
                                    formElement.parentNode.removeChild(formElement);
                                }
                                
                                console.log("Silent sync cleanup completed");
                            } catch (cleanupError) {
                                console.log("Silent sync cleanup error (non-critical):", cleanupError);
                            }
                        }, 2000);
                    };
                    
                    // Set up cleanup
                    iframe.onload = cleanupElements;
                    iframe.onerror = cleanupElements;
                    
                    // Add to document and submit
                    document.body.appendChild(iframe);
                    document.body.appendChild(form);
                    
                    // Submit the form
                    form.submit();
                    console.log("Silent backend sync form submitted");
                    
                    // Set a safety timeout for cleanup
                    setTimeout(cleanupElements, 5000);
                } catch (syncError) {
                    console.log("Silent sync setup error (non-critical):", syncError);
                }
            };
            
            // Attempt silent sync in the background
            setTimeout(() => {
                silentSync();
            }, 100);
            
        } catch (error) {
            console.error('Google login failed:', error);
            setError('Login failed. Please try again.');
        }
    };

    const handleLogout = async () => {
        try {
            await signOut(auth);
            await fetch('http://localhost:5000/auth/logout', {
                method: 'GET',
                credentials: 'include'
            });
            onLogout();
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    const handleForgotPassword = async (e) => {
        e.preventDefault();
        try {
            await sendPasswordResetEmail(auth, email);
            setSuccessMessage('Password reset email sent! Please check your inbox.');
            setError('');
            setIsForgotPassword(false);
        } catch (error) {
            setError(error.message);
            setSuccessMessage('');
        }
    };

    // Add function to resend verification email
    const handleResendVerification = async () => {
        try {
            const currentUser = auth.currentUser;
            if (currentUser && !currentUser.emailVerified) {
                await sendEmailVerification(currentUser);
                setSuccessMessage('Verification email resent! Please check your inbox.');
            }
        } catch (error) {
            setError(error.message);
        }
    };

    const handleDeleteAccount = async () => {
        try {
            const currentUser = auth.currentUser;
            if (!currentUser) {
                throw new Error('No user logged in');
            }
            
            // Get user info before deleting
            const token = await currentUser.getIdToken();
            const uid = currentUser.uid;
            
            // Create a hidden iframe to make the request silently
            // This avoids CORS errors in the console while still making the request
            const silentRequest = () => {
                try {
                    console.log("Silently requesting backend account deletion");
                    
                    // Use a direct fetch with no-cors mode which doesn't report errors in console
                    fetch('http://localhost:5000/auth/delete-account-silent', {
                        method: 'POST',
                        mode: 'no-cors', // This prevents CORS errors from appearing in console
                        cache: 'no-cache',
                        headers: {
                            'Content-Type': 'text/plain', // Using text/plain to avoid preflight
                        },
                        body: JSON.stringify({
                            token: token,
                            uid: uid
                        })
                    }).catch(() => {
                        // Silently ignore any errors - not logging them to avoid console messages
                    });
                    
                    console.log("Backend account deletion request sent silently");
                } catch (requestError) {
                    // Don't log the error to avoid console messages
                }
            };
            
            // Attempt to silently call the backend endpoint
            silentRequest();
            console.log("Backend account deletion request initiated");
            
            // Wait a moment to allow the request to be sent
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Then delete Firebase account
            console.log("Attempting to delete Firebase account");
            await deleteUser(currentUser);
            console.log("Firebase account deletion successful");
            
            // Logout and clear user state
            setShowDeleteConfirmation(false);
            onLogout();
            console.log("User logged out after account deletion");
        } catch (error) {
            console.error('Error deleting account:', error);
            setDeleteError(error.message);
        }
    };

    return (
        <div className="auth-container">
            {!user ? (
                <div className="auth-forms">
                    <div className="auth-tabs">
                        <button 
                            className={`auth-tab ${isLogin && !isForgotPassword ? 'active' : ''}`}
                            onClick={() => {
                                setIsLogin(true);
                                setIsForgotPassword(false);
                            }}
                        >
                            Login
                        </button>
                        <button 
                            className={`auth-tab ${!isLogin && !isForgotPassword ? 'active' : ''}`}
                            onClick={() => {
                                setIsLogin(false);
                                setIsForgotPassword(false);
                            }}
                        >
                            Register
                        </button>
                    </div>

                    {isForgotPassword ? (
                        <form onSubmit={handleForgotPassword}>
                            <h2>Reset Password</h2>
                            <p className="reset-instructions">
                                Enter your email address and we'll send you a link to reset your password.
                            </p>
                            <div className="form-group">
                                <input
                                    type="email"
                                    placeholder="Email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                            {error && <div className="error-message">{error}</div>}
                            {successMessage && <div className="success-message">{successMessage}</div>}
                            <button type="submit" className="auth-button">
                                Send Reset Link
                            </button>
                            <button 
                                type="button" 
                                className="back-to-login"
                                onClick={() => setIsForgotPassword(false)}
                            >
                                Back to Login
                            </button>
                        </form>
                    ) : (
                        <>
                            {verificationSent ? (
                                <div className="verification-sent">
                                    <h3>Verify Your Email</h3>
                                    <p>We've sent a verification link to your email address. Please check your inbox and click the link to verify your account.</p>
                                    <button 
                                        className="resend-button"
                                        onClick={handleResendVerification}
                                    >
                                        Resend Verification Email
                                    </button>
                                    <button 
                                        className="back-to-login"
                                        onClick={() => {
                                            setVerificationSent(false);
                                            setIsLogin(true);
                                        }}
                                    >
                                        Back to Login
                                    </button>
                                </div>
                            ) : (
                                <form onSubmit={isLogin ? handleFirebaseLogin : handleFirebaseRegister}>
                                    <div className="form-group">
                                        <input
                                            type="email"
                                            placeholder="Email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <input
                                            type="password"
                                            placeholder="Password"
                                            value={password}
                                            onChange={(e) => {
                                                setPassword(e.target.value);
                                                if (!isLogin) {
                                                    checkPasswordStrength(e.target.value);
                                                }
                                            }}
                                            required
                                        />
                                        {!isLogin && password && (
                                            <div className="password-requirements">
                                                <div className={`requirement ${passwordCriteria.length ? 'met' : ''}`}>
                                                    {passwordCriteria.length ? '✓' : '○'} At least 8 characters
                                                </div>
                                                <div className={`requirement ${passwordCriteria.uppercase ? 'met' : ''}`}>
                                                    {passwordCriteria.uppercase ? '✓' : '○'} One uppercase letter
                                                </div>
                                                <div className={`requirement ${passwordCriteria.lowercase ? 'met' : ''}`}>
                                                    {passwordCriteria.lowercase ? '✓' : '○'} One lowercase letter
                                                </div>
                                                <div className={`requirement ${passwordCriteria.number ? 'met' : ''}`}>
                                                    {passwordCriteria.number ? '✓' : '○'} One number
                                                </div>
                                                <div className={`requirement ${passwordCriteria.special ? 'met' : ''}`}>
                                                    {passwordCriteria.special ? '✓' : '○'} One special character
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                    {error && <div className="error-message">{error}</div>}
                                    <button type="submit" className="auth-button">
                                        {isLogin ? 'Login' : 'Register'}
                                    </button>
                                </form>
                            )}

                            {isLogin && (
                                <button 
                                    className="forgot-password"
                                    onClick={() => setIsForgotPassword(true)}
                                >
                                    Forgot Password?
                                </button>
                            )}

                            <div className="divider">
                                <span>or</span>
                            </div>

                            <div className="google-login-wrapper">
                                <button 
                                    onClick={handleGoogleLogin}
                                    className="google-login-button"
                                >
                                    Continue with Google
                                </button>
                            </div>
                        </>
                    )}
                </div>
            ) : (
                <div className="user-profile">
                    <img src={user.profile_pic} alt={user.name} className="profile-pic" />
                    <span className="user-name">{user.name}</span>
                    <div className="user-menu-container" ref={menuRef}>
                        <button 
                            className="menu-trigger"
                            onClick={() => setShowUserMenu(!showUserMenu)}
                        >
                            <svg className="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 5v14M5 12h14" />
                            </svg>
                        </button>
                        {showUserMenu && (
                            <div className="user-menu">
                                <button onClick={handleLogout} className="menu-item">
                                    <svg className="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                    </svg>
                                    Logout
                                </button>
                                <button 
                                    onClick={() => {
                                        setShowUserMenu(false);
                                        setShowDeleteConfirmation(true);
                                    }} 
                                    className="menu-item delete"
                                >
                                    <svg className="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                    Delete Account
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {showDeleteConfirmation && (
                <div className="delete-confirmation-modal">
                    <div className="delete-confirmation-content">
                        <h3>Delete Account</h3>
                        <p>Are you sure you want to delete your account? This action cannot be undone.</p>
                        {deleteError && <div className="error-message">{deleteError}</div>}
                        <div className="delete-confirmation-buttons">
                            <button 
                                onClick={handleDeleteAccount} 
                                className="confirm-delete-button"
                            >
                                Yes, Delete Account
                            </button>
                            <button 
                                onClick={() => setShowDeleteConfirmation(false)} 
                                className="cancel-delete-button"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Auth; 