import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { getAuth, 
         GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyD3SQxbl_WPLHQXKEYJdjaNY4YDsByEjI4",
  authDomain: "rotulo-checker.firebaseapp.com",
  projectId: "rotulo-checker",
  storageBucket: "rotulo-checker.firebasestorage.app",
  messagingSenderId: "405041107880",
  appId: "1:405041107880:web:5d3827ff7ed8cd5608439d",
  measurementId: "G-M2E0T677KY"
};

  // Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

const db = getFirestore(app);

export { auth, provider, db };