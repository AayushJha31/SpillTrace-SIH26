import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import Footer from "./components/Footer";

function App() {
  return (
    <BrowserRouter>
    <Header/>
    <div className="app-layout">
      <Sidebar/>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </div>
    <Footer/>
      
    </BrowserRouter>
  );
}

export default App;