import { PromptInput } from './components/PromptInput';

export default function App() {
  return (
    <div className="min-h-screen bg-huawei-gray-50 flex flex-col">
      <header className="bg-huawei-red shadow-sm flex-shrink-0">
        <div className="max-w-6xl mx-auto px-6 h-12 flex items-center justify-between">
          <span className="text-white text-sm font-semibold tracking-wide">HUAWEI CLOUD</span>
        </div>
      </header>

      <div className="bg-huawei-gray-50 border-b border-huawei-gray-200 flex-shrink-0">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div>
            <h1 className="text-lg font-bold text-huawei-gray-800">
              AI Privacy Gateway Demo — Huawei Cloud MaaS
            </h1>
          </div>
        </div>
      </div>

      <main className="flex-1 px-6 py-6">
        <PromptInput />
      </main>

      <footer className="text-center py-5 text-xs text-huawei-gray-300 border-t border-huawei-gray-100 bg-white flex-shrink-0">
        AI Privacy Gateway Demo — Huawei Cloud MaaS
      </footer>
    </div>
  );
}
