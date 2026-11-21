import { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import './AppLayout.css';

interface AppLayoutProps {
  children?: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="app-layout">
      <aside className="sidebar" role="navigation" aria-label="Main navigation">
        <nav>
          <ul className="nav-list">
            <li>
              <NavLink to="/learn" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Learn & Practice
              </NavLink>
            </li>
            <li>
              <NavLink to="/research" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Stock Research
              </NavLink>
            </li>
            <li>
              <NavLink to="/portfolio" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Portfolio Builder
              </NavLink>
            </li>
            <li>
              <NavLink to="/backtest" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Historical Analysis
              </NavLink>
            </li>
          </ul>
        </nav>
        <div className="sidebar-footer">
          <span className="version">WEAVE v0.1.0</span>
        </div>
      </aside>
      <main className="main-content" role="main">
        {children}
      </main>
    </div>
  );
}