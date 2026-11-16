import { createContext, useContext, useState, useEffect } from "react";
import { signInWithPopup, signOut, onAuthStateChanged } from "firebase/auth";
import { auth, googleProvider } from "../services/firebase";
import { api } from "../services/api";

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [idToken, setIdToken] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            setLoading(true);
            setError(null);
            if (firebaseUser) {
                try {
                    // Retrieve the security JWT token
                    const token = await firebaseUser.getIdToken(true);
                    setIdToken(token);

                    // Verify ID token on backend and retrieve db profile
                    const profile = await api.auth(token);
                    setUser({
                        uid: firebaseUser.uid,
                        email: firebaseUser.email,
                        displayName: firebaseUser.displayName || profile.name,
                        photoURL: firebaseUser.photoURL,
                        ...profile,
                        needs_subject_selection: true
                    });
                } catch (err) {
                    console.error("Auth verification error:", err);
                    setError(err.message || "Failed to verify credentials with server.");
                    // Sign out if verification fails
                    await signOut(auth);
                    setUser(null);
                    setIdToken(null);
                }
            } else {
                setUser(null);
                setIdToken(null);
            }
            setLoading(false);
        });

        return () => unsubscribe();
    }, []);

    const loginWithGoogle = async () => {
        setLoading(true);
        setError(null);
        try {
            await signInWithPopup(auth, googleProvider);
        } catch (err) {
            console.error("Google SSO Error:", err);
            setError(err.message || "Failed to sign in with Google.");
            setLoading(false);
        }
    };

    const logout = async () => {
        setLoading(true);
        try {
            await signOut(auth);
        } catch (err) {
            console.error("Logout Error:", err);
        }
        setLoading(false);
    };

    return (
        <AuthContext.Provider value={{ user, idToken, loading, error, loginWithGoogle, logout, setUser }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
