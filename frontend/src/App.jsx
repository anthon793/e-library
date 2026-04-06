import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Library from './pages/Library';
import BookDetail from './pages/BookDetail';
import ReadBook from './pages/ReadBook';
import Search from './pages/Search';
import Login from './pages/Login';
import Upload from './pages/Upload';
import ImportBooks from './pages/ImportBooks';
import AdminDashboard from './pages/AdminDashboard';
import GoogleBookDetail from './pages/GoogleBookDetail';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/library" replace />} />
        <Route path="/home" element={<Home />} />
        <Route path="/library" element={<Library />} />
        <Route path="/library/category/:slug" element={<Library />} />
        <Route path="/book/:id" element={<BookDetail />} />
        <Route path="/book/:id/read" element={<ReadBook />} />
        <Route path="/search" element={<Search />} />
        <Route path="/google-books/:volumeId" element={<GoogleBookDetail />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/import" element={<ImportBooks />} />
        <Route path="/admin" element={<AdminDashboard />} />
      </Route>
    </Routes>
  );
}
