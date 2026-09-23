import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Upload,
  MessageSquare,
  GitMerge,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Panel' },
  { to: '/invoices', icon: FileText, label: 'Facturas' },
  { to: '/upload', icon: Upload, label: 'Subir' },
  { to: '/chatbot', icon: MessageSquare, label: 'Chatbot' },
  { to: '/workflow', icon: GitMerge, label: 'Workflow' },
  { to: '/settings', icon: Settings, label: 'Configuración' },
];

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={`flex flex-col border-r border-gray-200 bg-gray-900 text-white transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Logo / Brand */}
      <div className="flex h-16 items-center justify-between border-b border-gray-700 px-4">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6 text-primary-400" />
            <span className="text-lg font-bold">OCR Facturas</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="rounded-md p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navItems.map(({ to, icon: Icon, label }) => {
          const isActive =
            to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);

          return (
            <NavLink
              key={to}
              to={to}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
              title={collapsed ? label : undefined}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="border-t border-gray-700 px-4 py-3">
          <p className="text-xs text-gray-500">OCR Facturas v1.0</p>
          <p className="text-xs text-gray-500">Facturación Argentina</p>
        </div>
      )}
    </aside>
  );
}
