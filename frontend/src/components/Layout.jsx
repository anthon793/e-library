import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const enforceMobileLanding = () => {
      if (window.innerWidth <= 768 && location.pathname === '/home') {
        navigate('/library', { replace: true });
      }
    };

    enforceMobileLanding();
    window.addEventListener('resize', enforceMobileLanding);
    return () => window.removeEventListener('resize', enforceMobileLanding);
  }, [location.pathname, navigate]);

  return (
    <div className="app-layout">
      <div className={`mobile-sidebar-backdrop ${mobileSidebarOpen ? 'open' : ''}`} onClick={() => setMobileSidebarOpen(false)} />
      <div className={`sidebar-shell ${mobileSidebarOpen ? 'open' : ''}`}>
        <Sidebar onNavigate={() => setMobileSidebarOpen(false)} />
      </div>
      <div className="app-main">
        <Topbar onToggleSidebar={() => setMobileSidebarOpen((v) => !v)} />
        <div className="app-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
