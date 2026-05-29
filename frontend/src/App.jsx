import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Trades from './pages/Trades';
import TradeDetail from './pages/TradeDetail';
import ImportCsv from './pages/ImportCsv';
import NT8 from './pages/NT8';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/trades" element={<Trades />} />
        <Route path="/trades/:id" element={<TradeDetail />} />
        <Route path="/import" element={<ImportCsv />} />
        <Route path="/nt8" element={<NT8 />} />
      </Route>
    </Routes>
  );
}
