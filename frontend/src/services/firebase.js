import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyAs6Xq1aNsWSC_xNft7KXLbwuOPM8-yGP4",
  authDomain: "ai-tutoring-agent.firebaseapp.com",
  projectId: "ai-tutoring-agent",
  storageBucket: "ai-tutoring-agent.firebasestorage.app",
  messagingSenderId: "906853126845",
  appId: "1:906853126845:web:8eddf865402b7e06901dd4"
};

// Initialize Firebase safely to prevent duplicate initialization during hot reloads
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);

// Initialize Services
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

export default app;
