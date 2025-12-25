import { format } from 'date-fns';
import { pl } from 'date-fns/locale';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: number;
  sources?: string[];
  requiresHuman?: boolean;
  timestamp: Date;
}

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-2xl ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`rounded-lg px-4 py-3 ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-white border border-gray-200 text-gray-900'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>

          {/* Assistant metadata */}
          {!isUser && message.confidence !== undefined && (
            <div className="mt-3 pt-3 border-t border-gray-100 space-y-2">
              {/* Confidence */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Pewność odpowiedzi:</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        message.confidence >= 0.8
                          ? 'bg-green-500'
                          : message.confidence >= 0.6
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${message.confidence * 100}%` }}
                    />
                  </div>
                  <span className="font-medium text-gray-700">
                    {(message.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Human required warning */}
              {message.requiresHuman && (
                <div className="flex items-center gap-2 text-xs text-orange-600 bg-orange-50 rounded px-2 py-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span>Może wymagać kontaktu z konsultantem</span>
                </div>
              )}

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <details className="text-xs">
                  <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                    Źródła ({message.sources.length})
                  </summary>
                  <ul className="mt-2 space-y-1 pl-4">
                    {message.sources.map((source, idx) => (
                      <li key={idx} className="text-gray-600">
                        • {source}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <p className="text-xs text-gray-400 mt-1 px-1">
          {format(message.timestamp, 'HH:mm', { locale: pl })}
        </p>
      </div>
    </div>
  );
}
