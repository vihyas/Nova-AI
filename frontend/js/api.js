/**
 * NOVA AI — API Client Module
 */
const API_BASE = window.location.origin;

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    if (options.body instanceof FormData) {
      delete defaultHeaders['Content-Type'];
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {})
      }
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  }

  // --- Chat & Agents ---
  async sendMessage(message, agentName = 'auto', sessionId = 'default', contextDocId = null) {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        agent_name: agentName,
        session_id: sessionId,
        context_document_id: contextDocId
      })
    });
  }

  async getChatHistory(sessionId = 'default') {
    return this.request(`/api/chat/history?session_id=${encodeURIComponent(sessionId)}`);
  }

  async clearChatHistory(sessionId = 'default') {
    return this.request(`/api/chat/history?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'DELETE'
    });
  }

  async getAgentLogs(limit = 20) {
    return this.request(`/api/chat/agents/logs?limit=${limit}`);
  }

  // --- Tasks ---
  async getTasks(filters = {}) {
    const query = new URLSearchParams(filters).toString();
    return this.request(`/api/tasks${query ? `?${query}` : ''}`);
  }

  async createTask(taskData) {
    return this.request('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(taskData)
    });
  }

  async parseTaskNaturalLanguage(text) {
    return this.request('/api/tasks/parse', {
      method: 'POST',
      body: JSON.stringify({ text })
    });
  }

  async updateTask(taskId, updates) {
    return this.request(`/api/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async deleteTask(taskId) {
    return this.request(`/api/tasks/${taskId}`, {
      method: 'DELETE'
    });
  }

  // --- Reminders ---
  async getReminders() {
    return this.request('/api/reminders');
  }

  async createReminder(reminderData) {
    return this.request('/api/reminders', {
      method: 'POST',
      body: JSON.stringify(reminderData)
    });
  }

  async updateReminderStatus(reminderId, status) {
    return this.request(`/api/reminders/${reminderId}/status?status=${encodeURIComponent(status)}`, {
      method: 'PUT'
    });
  }

  async deleteReminder(reminderId) {
    return this.request(`/api/reminders/${reminderId}`, {
      method: 'DELETE'
    });
  }

  // --- Documents (RAG) ---
  async uploadPdf(file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/api/documents/upload', {
      method: 'POST',
      body: formData
    });
  }

  async getDocuments() {
    return this.request('/api/documents');
  }

  async queryDocument(docId, query, topK = 4) {
    return this.request(`/api/documents/${docId}/query`, {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK })
    });
  }

  async getStudyGuide(docId) {
    return this.request(`/api/documents/${docId}/study-guide`);
  }

  async deleteDocument(docId) {
    return this.request(`/api/documents/${docId}`, {
      method: 'DELETE'
    });
  }

  // --- Memory ---
  async getMemories(category = null) {
    const query = category ? `?category=${encodeURIComponent(category)}` : '';
    return this.request(`/api/memory${query}`);
  }

  async addMemory(memoryData) {
    return this.request('/api/memory', {
      method: 'POST',
      body: JSON.stringify(memoryData)
    });
  }

  async updateMemory(memoryId, updates) {
    return this.request(`/api/memory/${memoryId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async deleteMemory(memoryId) {
    return this.request(`/api/memory/${memoryId}`, {
      method: 'DELETE'
    });
  }

  async exportMemories() {
    return this.request('/api/memory/export');
  }

  // --- Analytics ---
  async getProductivity() {
    return this.request('/api/analytics/productivity');
  }

  async getBenchmarks() {
    return this.request('/api/analytics/benchmarks');
  }

  // --- Settings ---
  async getSettings() {
    return this.request('/api/settings');
  }

  async updateSettings(settingsData) {
    return this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settingsData)
    });
  }
}

export const api = new ApiClient();

