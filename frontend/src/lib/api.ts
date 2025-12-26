/**
 * API client for E-commerce Support AI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SupportQuery {
  query: string;
  context?: Record<string, any>;
  language?: string;
}

interface SupportResponse {
  answer: string;
  confidence: number;
  sources: string[];
  requires_human: boolean;
  category?: string;
  timestamp: string;
}

interface Stats {
  total_queries: number;
  avg_confidence: number;
  automation_rate: number;
  automated_queries: number;
  human_required: number;
  categories: Record<string, number>;
}

class SupportAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Send a support query to the AI
   */
  async ask(query: string, context?: Record<string, any>): Promise<SupportResponse> {
    const response = await fetch(`${this.baseUrl}/support/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        context,
        language: 'pl',
      } as SupportQuery),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get statistics summary
   */
  async getStats(): Promise<Stats> {
    const response = await fetch(`${this.baseUrl}/metrics/summary`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; services: Record<string, string> }> {
    const response = await fetch(`${this.baseUrl}/health`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const supportAPI = new SupportAPI();
