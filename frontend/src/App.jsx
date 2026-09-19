import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Footer from "./components/Footer.jsx";
import Home from "./pages/Home.jsx";
import Analyze from "./pages/Analyze.jsx";
import Clinics from "./pages/Clinics.jsx";
import Learn from "./pages/Learn.jsx";

export default function App() {
  return (
    <>
      <Navbar />
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/clinics" element={<Clinics />} />
          <Route path="/learn" element={<Learn />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}
