import { api } from './api.js';
import { voice } from './voice.js';

// Application State
const state = {
  currentView: 'dashboard',
  selectedAgent: 'auto',
  activeDocId: null,
  tasks: [],
  reminders: [],
  memories: [],
  documents: [],
  settings: {},
  chatMessages: [],
  charts: {}
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupVoiceControls();
  setupTaskForms();
  setupDocumentUpload();
  setupSettingsForm();
  
  await loadInitialData();
  renderView('dashboard');
});

async function loadInitialData() {
  try {
    const [settings, tasks, reminders, memories, documents, history] = await Promise.all([
      api.getSettings(),
      api.getTasks(),
      api.getReminders(),
      api.getMemories(),
      api.getDocuments(),
      api.getChatHistory()
    ]);

    state.settings = settings;
    state.tasks = tasks;
    state.reminders = reminders;
    state.memories = memories;
    state.documents = documents;
    state.chatMessages = history;

    updateHeaderBadges();
  } catch (err) {
    console.error('Error loading initial data:', err);
    showToast('Failed to load initial data from server', 'error');
  }
}

// --- Navigation ---
function setupNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = link.getAttribute('data-view');
      renderView(target);
    });
  });
}

function renderView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('hidden'));
  
  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) {
    targetView.classList.remove('hidden');
  }

  // Highlight active link
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('data-view') === viewName) {
      link.classList.add('bg-indigo-600/30', 'text-indigo-400', 'border-indigo-500');
      link.classList.remove('text-slate-400', 'border-transparent');
    } else {
      link.classList.remove('bg-indigo-600/30', 'text-indigo-400', 'border-indigo-500');
      link.classList.add('text-slate-400', 'border-transparent');
    }
  });

  // Trigger view-specific renderers
  if (viewName === 'dashboard') renderDashboard();
  if (viewName === 'assistant') renderAssistant();
  if (viewName === 'tasks') renderTasks();
  if (viewName === 'calendar') renderCalendar();
  if (viewName === 'knowledge') renderKnowledge();
  if (viewName === 'memory') renderMemory();
  if (viewName === 'analytics') renderAnalytics();
  if (viewName === 'settings') renderSettings();
}

function updateHeaderBadges() {
  const providerBadge = document.getElementById('header-provider-badge');
  if (providerBadge && state.settings) {
    const prov = state.settings.default_provider || 'offline';
    providerBadge.textContent = prov.toUpperCase();
  }
}

// --- Toast Notifications ---
function showToast(message, type = 'info') {
  const toastContainer = document.getElementById('toast-container');
  if (!toastContainer) return;

  const toast = document.createElement('div');
  const bg = type === 'error' ? 'bg-red-900/90 border-red-500' : type === 'success' ? 'bg-emerald-900/90 border-emerald-500' : 'bg-indigo-900/90 border-indigo-500';
  toast.className = `${bg} border text-white px-4 py-3 rounded-lg shadow-xl text-sm flex items-center justify-between transition-all transform duration-300 translate-y-2`;
  toast.innerHTML = `<span>${message}</span><button class="ml-4 text-slate-400 hover:text-white">&times;</button>`;
  
  toast.querySelector('button').onclick = () => toast.remove();
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// --- Dashboard View ---
async function renderDashboard() {
  try {
    const metrics = await api.getProductivity();
    document.getElementById('dash-completion-rate').textContent = `${metrics.completion_rate}%`;
    document.getElementById('dash-velocity-score').textContent = `${metrics.velocity_score}`;
    document.getElementById('dash-total-tasks').textContent = metrics.total_tasks;
    document.getElementById('dash-urgent-tasks').textContent = metrics.urgent_tasks_count;

    // Render Today's Tasks
    const todayList = document.getElementById('dash-today-tasks');
    todayList.innerHTML = '';
    const pendingTasks = state.tasks.filter(t => t.status !== 'completed').slice(0, 5);
    if (pendingTasks.length === 0) {
      todayList.innerHTML = `<p class="text-slate-400 text-sm italic">All tasks completed! Great work today.</p>`;
    } else {
      pendingTasks.forEach(task => {
        const item = document.createElement('div');
        item.className = 'flex items-center justify-between p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800/80 transition';
        item.innerHTML = `
          <div class="flex items-center space-x-3">
            <input type="checkbox" data-task-id="${task.id}" class="task-checkbox rounded border-slate-600 text-indigo-600 focus:ring-indigo-500 h-4 w-4">
            <div>
              <p class="font-medium text-slate-200 text-sm">${escapeHtml(task.title)}</p>
              <p class="text-xs text-slate-400">${task.due_date ? new Date(task.due_date).toLocaleString() : 'No deadline'} · ${task.category}</p>
            </div>
          </div>
          <span class="px-2 py-0.5 text-xs rounded font-medium ${getPriorityBadgeClass(task.priority)}">${task.priority}</span>
        `;
        todayList.appendChild(item);
      });

      todayList.querySelectorAll('.task-checkbox').forEach(cb => {
        cb.onchange = async (e) => {
          const id = e.target.getAttribute('data-task-id');
          await api.updateTask(id, { status: 'completed' });
          showToast('Task marked as completed! 🎉', 'success');
          await loadInitialData();
          renderDashboard();
        };
      });
    }

    // Render Upcoming Reminders
    const remindersList = document.getElementById('dash-reminders-list');
    remindersList.innerHTML = '';
    const activeReminders = state.reminders.filter(r => r.status === 'pending').slice(0, 4);
    if (activeReminders.length === 0) {
      remindersList.innerHTML = `<p class="text-slate-400 text-sm italic">No upcoming reminders.</p>`;
    } else {
      activeReminders.forEach(r => {
        const item = document.createElement('div');
        item.className = 'flex items-center justify-between p-3 rounded-lg bg-slate-800/40 border border-slate-700/50';
        item.innerHTML = `
          <div>
            <p class="text-sm font-medium text-slate-200">${escapeHtml(r.title)}</p>
            <p class="text-xs text-indigo-400">⏰ ${new Date(r.remind_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · ${r.recurrence}</p>
          </div>
          <button data-reminder-id="${r.id}" class="dismiss-reminder-btn text-xs text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-700/50 hover:bg-slate-700">Dismiss</button>
        `;
        remindersList.appendChild(item);
      });

      remindersList.querySelectorAll('.dismiss-reminder-btn').forEach(btn => {
        btn.onclick = async (e) => {
          const id = e.target.getAttribute('data-reminder-id');
          await api.updateReminderStatus(id, 'dismissed');
          showToast('Reminder dismissed', 'info');
          await loadInitialData();
          renderDashboard();
        };
      });
    }

    // Render Agent Activity Logs
    const logs = await api.getAgentLogs(8);
    const logContainer = document.getElementById('dash-agent-logs');
    logContainer.innerHTML = '';
    logs.forEach(l => {
      const row = document.createElement('div');
      row.className = 'flex items-center justify-between text-xs py-2 border-b border-slate-800 text-slate-400';
      row.innerHTML = `
        <div class="flex items-center space-x-2">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span class="font-medium text-slate-300">${escapeHtml(l.agent_name)}</span>
          <span>${escapeHtml(l.action)}</span>
        </div>
        <div class="text-slate-500">${l.execution_time_ms}ms</div>
      `;
      logContainer.appendChild(row);
    });

  } catch (err) {
    console.error('Error rendering dashboard:', err);
  }
}

// --- Voice & Assistant Controls ---
function setupVoiceControls() {
  const micButton = document.getElementById('chat-mic-btn');
  const chatInput = document.getElementById('chat-input');
  const voiceWave = document.getElementById('voice-status-indicator');

  if (micButton) {
    micButton.onclick = () => {
      voice.toggleListening(
        (transcript) => {
          if (transcript.interim) {
            chatInput.placeholder = transcript.interim;
          }
          if (transcript.final) {
            chatInput.value = transcript.final;
            chatInput.placeholder = 'Message NOVA or speak...';
            // Auto submit speech command
            handleSendMessage();
          }
        },
        (state) => {
          if (state === 'listening') {
            micButton.classList.add('voice-recording-active');
            if (voiceWave) voiceWave.classList.remove('hidden');
          } else {
            micButton.classList.remove('voice-recording-active');
            if (voiceWave) voiceWave.classList.add('hidden');
          }
        }
      );
    };
  }

  const sendBtn = document.getElementById('chat-send-btn');
  if (sendBtn) {
    sendBtn.onclick = handleSendMessage;
  }

  if (chatInput) {
    chatInput.onkeydown = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    };
  }

  // Quick Action Buttons
  document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
    btn.onclick = () => {
      const text = btn.getAttribute('data-prompt');
      const input = document.getElementById('chat-input');
      if (input) {
        input.value = text;
        handleSendMessage();
      }
    };
  });

  // Agent selector dropdown/pills
  document.querySelectorAll('.agent-pill-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.agent-pill-btn').forEach(b => {
        b.classList.remove('bg-indigo-600', 'text-white');
        b.classList.add('bg-slate-800', 'text-slate-400');
      });
      btn.classList.add('bg-indigo-600', 'text-white');
      btn.classList.remove('bg-slate-800', 'text-slate-400');
      state.selectedAgent = btn.getAttribute('data-agent');
    };
  });

  // Clear chat
  const clearBtn = document.getElementById('clear-chat-btn');
  if (clearBtn) {
    clearBtn.onclick = async () => {
      await api.clearChatHistory();
      state.chatMessages = [];
      renderAssistant();
      showToast('Chat history cleared', 'info');
    };
  }
}

async function handleSendMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message) return;

  input.value = '';

  // Append user message immediately
  appendChatMessage({
    role: 'user',
    content: message,
    agent_name: 'You'
  });

  // Show typing loader
  const chatBox = document.getElementById('chat-messages-container');
  const loader = document.createElement('div');
  loader.id = 'typing-loader';
  loader.className = 'flex items-center space-x-2 text-slate-400 text-xs py-2';
  loader.innerHTML = `
    <div class="w-2 h-2 rounded-full bg-indigo-500 animate-bounce"></div>
    <div class="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style="animation-delay: 0.2s"></div>
    <div class="w-2 h-2 rounded-full bg-pink-500 animate-bounce" style="animation-delay: 0.4s"></div>
    <span class="ml-2 font-medium">NOVA is processing...</span>
  `;
  chatBox.appendChild(loader);
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await api.sendMessage(
      message,
      state.selectedAgent,
      'default',
      state.activeDocId
    );

    loader.remove();

    appendChatMessage({
      role: 'assistant',
      content: response.reply,
      agent_name: response.agent_name,
      tools: response.triggered_tools,
      sources: response.rag_sources
    });

    // Voice response if enabled
    const voiceToggle = document.getElementById('enable-tts-toggle');
    if (voiceToggle && voiceToggle.checked && response.audio_text) {
      voice.speak(response.audio_text);
    }

    // Refresh tasks and memories if modified
    await loadInitialData();

  } catch (err) {
    loader.remove();
    showToast(`Error: ${err.message}`, 'error');
  }
}

function renderAssistant() {
  const chatBox = document.getElementById('chat-messages-container');
  if (!chatBox) return;
  chatBox.innerHTML = '';

  if (state.chatMessages.length === 0) {
    chatBox.innerHTML = `
      <div class="text-center py-12 text-slate-400">
        <div class="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-4 text-indigo-400 text-2xl">✨</div>
        <h3 class="text-lg font-semibold text-white mb-2">Welcome to NOVA AI</h3>
        <p class="text-sm max-w-md mx-auto mb-6">Ask questions, manage tasks with natural language, analyze PDFs, or speak commands through your microphone.</p>
        <div class="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
          <button class="quick-prompt-btn px-3 py-1.5 rounded-full bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300" data-prompt="Create a task to study Java for two hours tomorrow at 6 PM">Study Java tomorrow at 6 PM</button>
          <button class="quick-prompt-btn px-3 py-1.5 rounded-full bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300" data-prompt="Explain linked lists in Java">Explain linked lists</button>
          <button class="quick-prompt-btn px-3 py-1.5 rounded-full bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300" data-prompt="What are my saved learning goals?">Check my memory goals</button>
          <button class="quick-prompt-btn px-3 py-1.5 rounded-full bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300" data-prompt="Show my productivity velocity">Show productivity stats</button>
        </div>
      </div>
    `;
    setupVoiceControls();
    return;
  }

  state.chatMessages.forEach(msg => {
    appendChatMessage(msg);
  });
}

function appendChatMessage(msg) {
  const chatBox = document.getElementById('chat-messages-container');
  if (!chatBox) return;

  const isUser = msg.role === 'user';
  const row = document.createElement('div');
  row.className = `flex flex-col mb-4 ${isUser ? 'items-end' : 'items-start'}`;

  let toolsHtml = '';
  if (msg.tools && msg.tools.length > 0) {
    toolsHtml = `
      <div class="mt-2 space-y-1">
        ${msg.tools.map(t => `
          <div class="flex items-center text-xs bg-slate-900/60 border border-emerald-500/30 text-emerald-400 px-2.5 py-1 rounded">
            <span class="mr-1.5">⚡ Tool Executed:</span> <strong>${escapeHtml(t.tool_name)}</strong> (${escapeHtml(t.action)})
          </div>
        `).join('')}
      </div>
    `;
  }

  let citationsHtml = '';
  if (msg.sources && msg.sources.length > 0) {
    citationsHtml = `
      <div class="mt-2 pt-2 border-t border-slate-700/40 text-xs text-slate-400">
        <p class="font-semibold text-slate-300 mb-1">📚 Referenced Document Passages:</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-1.5">
          ${msg.sources.map(s => `
            <div class="p-1.5 rounded bg-slate-900/50 border border-slate-800 text-[11px]">
              <span class="text-indigo-400 font-bold">Page ${s.page}:</span> ${escapeHtml(s.excerpt)}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  const bubbleClass = isUser
    ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%] shadow-lg'
    : 'glass-card text-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[85%] border border-slate-700/60 shadow-lg';

  row.innerHTML = `
    <div class="flex items-center space-x-2 mb-1 px-1">
      <span class="text-xs font-semibold ${isUser ? 'text-indigo-400' : 'text-purple-400'}">${escapeHtml(msg.agent_name || (isUser ? 'You' : 'NOVA'))}</span>
    </div>
    <div class="${bubbleClass}">
      <div class="prose prose-invert text-sm max-w-none whitespace-pre-line leading-relaxed">${formatMarkdown(msg.content)}</div>
      ${toolsHtml}
      ${citationsHtml}
      ${!isUser ? `
        <div class="mt-2 flex items-center justify-end space-x-2 text-slate-400">
          <button class="speak-msg-btn text-xs hover:text-white p-1 rounded hover:bg-slate-700/50" title="Listen to message">🔊</button>
        </div>
      ` : ''}
    </div>
  `;

  if (!isUser) {
    const speakBtn = row.querySelector('.speak-msg-btn');
    if (speakBtn) {
      speakBtn.onclick = () => {
        voice.speak(msg.content);
      };
    }
  }

  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// --- Task Manager ---
function setupTaskForms() {
  // Quick natural language input bar
  const nlInput = document.getElementById('nl-task-input');
  const nlBtn = document.getElementById('nl-task-submit');
  if (nlBtn && nlInput) {
    nlBtn.onclick = async () => {
      const text = nlInput.value.trim();
      if (!text) return;
      try {
        const res = await api.parseTaskNaturalLanguage(text);
        if (res.success && res.parsed_task) {
          await api.createTask(res.parsed_task);
          showToast(`Task created: "${res.parsed_task.title}"`, 'success');
          nlInput.value = '';
          await loadInitialData();
          renderTasks();
          renderDashboard();
        } else {
          showToast(res.explanation, 'error');
        }
      } catch (err) {
        showToast(err.message, 'error');
      }
    };

    nlInput.onkeydown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        nlBtn.click();
      }
    };
  }

  // Structured Task Modal & Filters
  const newTaskBtn = document.getElementById('open-create-task-modal');
  const taskModal = document.getElementById('create-task-modal');
  const closeModalBtn = document.getElementById('close-task-modal');
  const taskForm = document.getElementById('create-task-form');

  if (newTaskBtn && taskModal) {
    newTaskBtn.onclick = () => taskModal.classList.remove('hidden');
  }
  if (closeModalBtn && taskModal) {
    closeModalBtn.onclick = () => taskModal.classList.add('hidden');
  }

  if (taskForm) {
    taskForm.onsubmit = async (e) => {
      e.preventDefault();
      const formData = new FormData(taskForm);
      const data = {
        title: formData.get('title'),
        description: formData.get('description'),
        priority: formData.get('priority'),
        category: formData.get('category'),
        duration_minutes: parseInt(formData.get('duration_minutes') || 30),
        due_date: formData.get('due_date') || null,
        tags: formData.get('tags') || ''
      };

      try {
        await api.createTask(data);
        showToast('Task created successfully!', 'success');
        taskForm.reset();
        taskModal.classList.add('hidden');
        await loadInitialData();
        renderTasks();
      } catch (err) {
        showToast(err.message, 'error');
      }
    };
  }

  // Filter tabs
  document.querySelectorAll('.task-filter-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.task-filter-btn').forEach(b => {
        b.classList.remove('bg-indigo-600', 'text-white');
        b.classList.add('bg-slate-800', 'text-slate-400');
      });
      btn.classList.add('bg-indigo-600', 'text-white');
      btn.classList.remove('bg-slate-800', 'text-slate-400');
      renderTasks(btn.getAttribute('data-filter'));
    };
  });
}

function renderTasks(filter = 'all') {
  const container = document.getElementById('tasks-list-container');
  if (!container) return;
  container.innerHTML = '';

  let filtered = [...state.tasks];
  if (filter === 'pending') filtered = filtered.filter(t => t.status === 'pending');
  if (filter === 'in_progress') filtered = filtered.filter(t => t.status === 'in_progress');
  if (filter === 'completed') filtered = filtered.filter(t => t.status === 'completed');
  if (filter === 'urgent') filtered = filtered.filter(t => t.priority === 'urgent');

  if (filtered.length === 0) {
    container.innerHTML = `<p class="text-center py-10 text-slate-500 text-sm">No tasks found matching this view.</p>`;
    return;
  }

  filtered.forEach(t => {
    const isCompleted = t.status === 'completed';
    const card = document.createElement('div');
    card.className = `p-4 rounded-xl border ${isCompleted ? 'bg-slate-900/30 border-slate-800 opacity-75' : 'bg-slate-800/40 border-slate-700/60'} hover:border-indigo-500/50 transition flex flex-col justify-between`;
    card.innerHTML = `
      <div>
        <div class="flex items-start justify-between">
          <div class="flex items-start space-x-3">
            <input type="checkbox" ${isCompleted ? 'checked' : ''} data-id="${t.id}" class="task-toggle-cb mt-1 rounded border-slate-600 text-indigo-600 focus:ring-indigo-500 h-4 w-4">
            <div>
              <h4 class="font-semibold text-slate-100 ${isCompleted ? 'line-through text-slate-400' : ''}">${escapeHtml(t.title)}</h4>
              ${t.description ? `<p class="text-xs text-slate-400 mt-1">${escapeHtml(t.description)}</p>` : ''}
            </div>
          </div>
          <span class="px-2 py-0.5 text-xs rounded font-medium ${getPriorityBadgeClass(t.priority)}">${t.priority}</span>
        </div>

        <div class="flex flex-wrap gap-2 mt-4 text-xs text-slate-400">
          <span class="bg-slate-700/40 px-2 py-0.5 rounded">📂 ${t.category}</span>
          <span class="bg-slate-700/40 px-2 py-0.5 rounded">⏱️ ${t.duration_minutes} mins</span>
          ${t.due_date ? `<span class="bg-slate-700/40 px-2 py-0.5 rounded">📅 ${new Date(t.due_date).toLocaleString()}</span>` : ''}
          ${t.tags ? `<span class="bg-slate-700/40 px-2 py-0.5 rounded">🏷️ ${t.tags}</span>` : ''}
        </div>
      </div>

      <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-700/40 text-xs">
        <select data-id="${t.id}" class="task-status-select bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-300 text-xs">
          <option value="pending" ${t.status === 'pending' ? 'selected' : ''}>Pending</option>
          <option value="in_progress" ${t.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
          <option value="completed" ${t.status === 'completed' ? 'selected' : ''}>Completed</option>
        </select>
        <button data-id="${t.id}" class="task-delete-btn text-rose-400 hover:text-rose-300 px-2 py-1">Delete</button>
      </div>
    `;
    container.appendChild(card);
  });

  // Event handlers
  container.querySelectorAll('.task-toggle-cb').forEach(cb => {
    cb.onchange = async (e) => {
      const id = e.target.getAttribute('data-id');
      const newStatus = e.target.checked ? 'completed' : 'pending';
      await api.updateTask(id, { status: newStatus });
      await loadInitialData();
      renderTasks(filter);
    };
  });

  container.querySelectorAll('.task-status-select').forEach(sel => {
    sel.onchange = async (e) => {
      const id = e.target.getAttribute('data-id');
      await api.updateTask(id, { status: e.target.value });
      await loadInitialData();
      renderTasks(filter);
    };
  });

  container.querySelectorAll('.task-delete-btn').forEach(btn => {
    btn.onclick = async (e) => {
      const id = e.target.getAttribute('data-id');
      if (confirm('Delete this task?')) {
        await api.deleteTask(id);
        showToast('Task deleted', 'info');
        await loadInitialData();
        renderTasks(filter);
      }
    };
  });
}

// --- Calendar & Reminders View ---
function renderCalendar() {
  const container = document.getElementById('calendar-reminders-list');
  if (!container) return;
  container.innerHTML = '';

  state.reminders.forEach(r => {
    const isDismissed = r.status === 'dismissed';
    const card = document.createElement('div');
    card.className = `p-3 rounded-lg border ${isDismissed ? 'bg-slate-900/30 border-slate-800 opacity-60' : 'bg-slate-800/40 border-slate-700'} flex items-center justify-between`;
    card.innerHTML = `
      <div>
        <h5 class="text-sm font-semibold text-slate-200">${escapeHtml(r.title)}</h5>
        <p class="text-xs text-indigo-400">⏰ ${new Date(r.remind_at).toLocaleString()} · Recurrence: ${r.recurrence}</p>
      </div>
      <div class="flex items-center space-x-2">
        <button data-id="${r.id}" class="cal-dismiss-btn text-xs px-2.5 py-1 rounded bg-slate-700 text-slate-300 hover:bg-slate-600">
          ${isDismissed ? 'Restore' : 'Dismiss'}
        </button>
        <button data-id="${r.id}" class="cal-delete-btn text-xs text-rose-400 hover:text-rose-300 px-2 py-1">Delete</button>
      </div>
    `;
    container.appendChild(card);
  });

  container.querySelectorAll('.cal-dismiss-btn').forEach(btn => {
    btn.onclick = async (e) => {
      const id = e.target.getAttribute('data-id');
      const reminder = state.reminders.find(r => r.id === parseInt(id));
      const newStatus = reminder && reminder.status === 'dismissed' ? 'pending' : 'dismissed';
      await api.updateReminderStatus(id, newStatus);
      await loadInitialData();
      renderCalendar();
    };
  });

  container.querySelectorAll('.cal-delete-btn').forEach(btn => {
    btn.onclick = async (e) => {
      const id = e.target.getAttribute('data-id');
      await api.deleteReminder(id);
      showToast('Reminder removed', 'info');
      await loadInitialData();
      renderCalendar();
    };
  });

  // Calendar schedule grid
  const scheduleBox = document.getElementById('calendar-schedule-grid');
  if (scheduleBox) {
    scheduleBox.innerHTML = '';
    const now = new Date();
    for (let i = 0; i < 7; i++) {
      const day = new Date(now);
      day.setDate(now.getDate() + i);
      const dayStr = day.toISOString().split('T')[0];
      const dayTasks = state.tasks.filter(t => t.due_date && t.due_date.startsWith(dayStr));

      const col = document.createElement('div');
      col.className = 'p-3 rounded-lg bg-slate-800/30 border border-slate-700/50 min-h-[140px] flex flex-col justify-between';
      col.innerHTML = `
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-300">${day.toLocaleDateString([], { weekday: 'short' })}</span>
            <span class="text-xs text-indigo-400">${day.getDate()}</span>
          </div>
          <div class="space-y-1">
            ${dayTasks.map(t => `
              <div class="text-[11px] p-1 rounded bg-indigo-950/60 border border-indigo-700/40 text-indigo-300 truncate" title="${escapeHtml(t.title)}">
                ${escapeHtml(t.title)}
              </div>
            `).join('')}
            ${dayTasks.length === 0 ? '<p class="text-[11px] text-slate-600 italic">No events</p>' : ''}
          </div>
        </div>
      `;
      scheduleBox.appendChild(col);
    }
  }

  // Create reminder form
  const remForm = document.getElementById('create-reminder-form');
  if (remForm) {
    remForm.onsubmit = async (e) => {
      e.preventDefault();
      const title = document.getElementById('rem-title').value.trim();
      const remindAt = document.getElementById('rem-datetime').value;
      const recurrence = document.getElementById('rem-recurrence').value;

      if (!title || !remindAt) return;
      await api.createReminder({ title, remind_at: remindAt, recurrence });
      showToast('Reminder scheduled!', 'success');
      remForm.reset();
      await loadInitialData();
      renderCalendar();
    };
  }
}

// --- Knowledge Hub / Document Intelligence ---
function setupDocumentUpload() {
  const fileInput = document.getElementById('pdf-file-input');
  const uploadArea = document.getElementById('pdf-drop-zone');
  const queryBtn = document.getElementById('doc-query-btn');
  const queryInput = document.getElementById('doc-query-input');

  if (uploadArea && fileInput) {
    uploadArea.onclick = () => fileInput.click();
    fileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('Please upload a PDF file', 'error');
        return;
      }

      showToast(`Uploading and indexing "${file.name}"...`, 'info');
      try {
        const doc = await api.uploadPdf(file);
        showToast(`Indexed ${doc.page_count} pages!`, 'success');
        await loadInitialData();
        renderKnowledge();
      } catch (err) {
        showToast(err.message, 'error');
      }
    };
  }

  if (queryBtn && queryInput) {
    queryBtn.onclick = handleDocQuery;
    queryInput.onkeydown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleDocQuery();
      }
    };
  }
}

async function handleDocQuery() {
  const queryInput = document.getElementById('doc-query-input');
  const query = queryInput.value.trim();
  if (!query) return;

  const resultsBox = document.getElementById('doc-query-results');
  resultsBox.innerHTML = `
    <div class="text-center py-6 text-indigo-400">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-2 border-indigo-500 border-t-transparent mb-2"></div>
      <p class="text-xs">Searching semantic chunks and citing pages...</p>
    </div>
  `;

  try {
    const docId = state.activeDocId || (state.documents[0] ? state.documents[0].id : null);
    if (!docId) {
      showToast('Please upload or select a document first', 'error');
      return;
    }

    const res = await api.queryDocument(docId, query);
    resultsBox.innerHTML = `
      <div class="p-4 rounded-xl bg-slate-800/80 border border-slate-700">
        <h4 class="text-sm font-semibold text-indigo-400 mb-2">Q: ${escapeHtml(res.query)}</h4>
        <div class="prose prose-invert text-sm text-slate-200 mb-4 whitespace-pre-line">${formatMarkdown(res.answer)}</div>
        
        <h5 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Supporting Citations:</h5>
        <div class="space-y-2">
          ${res.citations.map(c => `
            <div class="p-2.5 rounded bg-slate-900 border border-slate-800 text-xs">
              <span class="text-indigo-400 font-bold">📄 Page ${c.page} (Score: ${c.relevance_score}):</span>
              <p class="text-slate-400 mt-1 italic">"${escapeHtml(c.excerpt)}"</p>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch (err) {
    resultsBox.innerHTML = `<p class="text-rose-400 text-xs p-4">${err.message}</p>`;
  }
}

function renderKnowledge() {
  const listContainer = document.getElementById('documents-list');
  if (!listContainer) return;
  listContainer.innerHTML = '';

  if (state.documents.length === 0) {
    listContainer.innerHTML = `<p class="text-slate-500 text-sm italic">No PDF documents uploaded yet. Drop one above to get started!</p>`;
    return;
  }

  state.documents.forEach(doc => {
    const isSelected = state.activeDocId === doc.id;
    const card = document.createElement('div');
    card.className = `p-4 rounded-xl border ${isSelected ? 'bg-indigo-900/30 border-indigo-500' : 'bg-slate-800/40 border-slate-700/60'} hover:border-indigo-400/50 transition cursor-pointer`;
    card.innerHTML = `
      <div class="flex items-start justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-lg bg-red-500/20 text-red-400 flex items-center justify-center font-bold text-sm">PDF</div>
          <div>
            <h4 class="font-semibold text-slate-100 text-sm">${escapeHtml(doc.original_name)}</h4>
            <p class="text-xs text-slate-400">${(doc.file_size / 1024).toFixed(1)} KB · ${doc.page_count} Pages</p>
          </div>
        </div>
        <button data-id="${doc.id}" class="doc-delete-btn text-rose-400 hover:text-rose-300 text-xs p-1">Delete</button>
      </div>

      <p class="text-xs text-slate-300 mt-3 line-clamp-2">${escapeHtml(doc.summary)}</p>

      <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-700/40 text-xs">
        <button data-id="${doc.id}" class="doc-select-btn px-2.5 py-1 rounded ${isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}">
          ${isSelected ? 'Selected' : 'Select for Q&A'}
        </button>
        <button data-id="${doc.id}" class="doc-guide-btn text-indigo-400 hover:underline">Study Guide & Qs</button>
      </div>
    `;

    card.querySelector('.doc-select-btn').onclick = (e) => {
      e.stopPropagation();
      state.activeDocId = doc.id;
      renderKnowledge();
      showToast(`Selected "${doc.original_name}"`, 'info');
    };

    card.querySelector('.doc-guide-btn').onclick = async (e) => {
      e.stopPropagation();
      await openStudyGuide(doc.id);
    };

    card.querySelector('.doc-delete-btn').onclick = async (e) => {
      e.stopPropagation();
      if (confirm(`Delete document "${doc.original_name}"?`)) {
        await api.deleteDocument(doc.id);
        if (state.activeDocId === doc.id) state.activeDocId = null;
        showToast('Document deleted', 'info');
        await loadInitialData();
        renderKnowledge();
      }
    };

    listContainer.appendChild(card);
  });
}

async function openStudyGuide(docId) {
  try {
    const guide = await api.getStudyGuide(docId);
    const modal = document.getElementById('study-guide-modal');
    const content = document.getElementById('study-guide-content');
    if (!modal || !content) return;

    content.innerHTML = `
      <h3 class="text-lg font-bold text-white mb-2">${escapeHtml(guide.document_name)}</h3>
      <p class="text-sm text-slate-300 mb-4 bg-slate-900/60 p-3 rounded-lg border border-slate-800">${escapeHtml(guide.summary)}</p>

      <h4 class="font-bold text-xs uppercase tracking-wider text-indigo-400 mb-2">Key Extracted Points:</h4>
      <div class="space-y-1 mb-4 text-xs text-slate-300">
        ${guide.key_points.map(k => `<div>${escapeHtml(k)}</div>`).join('')}
      </div>

      <h4 class="font-bold text-xs uppercase tracking-wider text-purple-400 mb-2">Important Dates & Milestones:</h4>
      <div class="space-y-1 mb-4 text-xs text-slate-300">
        ${guide.important_dates_and_milestones.map(m => `<div>• ${escapeHtml(m)}</div>`).join('')}
      </div>

      <h4 class="font-bold text-xs uppercase tracking-wider text-emerald-400 mb-2">Sample Exam / Study Questions:</h4>
      <div class="space-y-2 text-xs">
        ${guide.study_questions.map((q, idx) => `
          <div class="p-2.5 rounded bg-slate-900 border border-slate-800">
            <p class="font-medium text-slate-200">Q${idx+1}: ${escapeHtml(q.question)}</p>
            <span class="text-emerald-400 font-semibold mt-1 inline-block">Ref: ${escapeHtml(q.answer_page)}</span>
          </div>
        `).join('')}
      </div>
    `;

    modal.classList.remove('hidden');
    document.getElementById('close-guide-modal').onclick = () => modal.classList.add('hidden');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// --- Memory Vault View ---
function renderMemory() {
  const container = document.getElementById('memory-cards-container');
  if (!container) return;
  container.innerHTML = '';

  state.memories.forEach(m => {
    const card = document.createElement('div');
    card.className = 'p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between';
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="px-2 py-0.5 text-xs rounded font-medium bg-purple-900/50 text-purple-300 border border-purple-500/30">${m.category}</span>
          <span class="text-xs text-slate-500">${(m.confidence * 100).toFixed(0)}% confidence</span>
        </div>
        <h5 class="text-sm font-semibold text-slate-200">${escapeHtml(m.key.replace('_', ' ').toUpperCase())}</h5>
        <p class="text-xs text-indigo-300 mt-1">${escapeHtml(m.value)}</p>
      </div>

      <div class="flex items-center justify-end space-x-2 mt-4 pt-3 border-t border-slate-700/40 text-xs">
        <button data-id="${m.id}" class="memory-delete-btn text-rose-400 hover:text-rose-300">Delete</button>
      </div>
    `;

    card.querySelector('.memory-delete-btn').onclick = async () => {
      await api.deleteMemory(m.id);
      showToast('Memory item deleted', 'info');
      await loadInitialData();
      renderMemory();
    };

    container.appendChild(card);
  });

  // Export button
  const exportBtn = document.getElementById('export-memory-btn');
  if (exportBtn) {
    exportBtn.onclick = async () => {
      const res = await api.exportMemories();
      const blob = new Blob([res.markdown_format], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'nova_personal_memories.md';
      a.click();
      showToast('Memories exported as Markdown!', 'success');
    };
  }

  // Add memory modal/form
  const addMemoryForm = document.getElementById('add-memory-form');
  if (addMemoryForm) {
    addMemoryForm.onsubmit = async (e) => {
      e.preventDefault();
      const cat = document.getElementById('mem-category').value;
      const key = document.getElementById('mem-key').value.trim();
      const val = document.getElementById('mem-val').value.trim();
      if (!key || !val) return;

      await api.addMemory({ category: cat, key, value: val, confidence: 1.0 });
      showToast('Memory recorded!', 'success');
      addMemoryForm.reset();
      await loadInitialData();
      renderMemory();
    };
  }
}

// --- Productivity Analytics View ---
async function renderAnalytics() {
  try {
    const metrics = await api.getProductivity();
    const benchmarks = await api.getBenchmarks();

    // Coaching Insights
    const coachingBox = document.getElementById('analytics-coaching-list');
    if (coachingBox) {
      coachingBox.innerHTML = metrics.ai_coaching_insights.map(i => `
        <div class="p-3 rounded-lg bg-indigo-950/40 border border-indigo-700/40 text-xs text-indigo-200">
          ${escapeHtml(i)}
        </div>
      `).join('');
    }

    // Evaluation Benchmarks
    const benchBox = document.getElementById('analytics-benchmarks-list');
    if (benchBox) {
      benchBox.innerHTML = `
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span class="text-xs text-slate-400">Task Execution</span>
            <p class="text-lg font-bold text-emerald-400">${benchmarks.task_execution_accuracy}</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span class="text-xs text-slate-400">Intent Classification</span>
            <p class="text-lg font-bold text-indigo-400">${benchmarks.intent_classification_accuracy}</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span class="text-xs text-slate-400">Retrieval MRR</span>
            <p class="text-lg font-bold text-purple-400">${benchmarks.document_retrieval_mrr}</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span class="text-xs text-slate-400">Avg Latency</span>
            <p class="text-lg font-bold text-cyan-400">${benchmarks.average_response_latency_ms} ms</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span class="text-xs text-slate-400">Voice Recognition</span>
            <p class="text-lg font-bold text-amber-400">${benchmarks.voice_recognition_accuracy}</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span class="text-xs text-slate-400">Reliability</span>
            <p class="text-lg font-bold text-emerald-400">${benchmarks.system_uptime_reliability}</p>
          </div>
        </div>
      `;
    }

    // Render Chart.js graphs
    renderCharts(metrics);

  } catch (err) {
    console.error('Error rendering analytics:', err);
  }
}

function renderCharts(metrics) {
  if (typeof Chart === 'undefined') return;

  // Trend Chart
  const trendCtx = document.getElementById('trend-chart')?.getContext('2d');
  if (trendCtx) {
    if (state.charts.trend) state.charts.trend.destroy();
    state.charts.trend = new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: metrics.daily_completion_trend.map(d => d.day),
        datasets: [{
          label: 'Completed Tasks',
          data: metrics.daily_completion_trend.map(d => d.completed),
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.15)',
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
          x: { grid: { color: 'rgba(255,255,255,0.05)' } }
        }
      }
    });
  }

  // Category Doughnut Chart
  const catCtx = document.getElementById('category-chart')?.getContext('2d');
  if (catCtx) {
    if (state.charts.cat) state.charts.cat.destroy();
    const categories = Object.keys(metrics.category_distribution);
    const counts = Object.values(metrics.category_distribution);

    state.charts.cat = new Chart(catCtx, {
      type: 'doughnut',
      data: {
        labels: categories.length ? categories : ['None'],
        datasets: [{
          data: counts.length ? counts : [1],
          backgroundColor: ['#6366f1', '#a855f7', '#ec4899', '#06b6d4', '#10b981']
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } }
      }
    });
  }
}

// --- Settings View ---
function setupSettingsForm() {
  const form = document.getElementById('settings-form');
  if (!form) return;

  form.onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const data = {
      default_provider: formData.get('default_provider'),
      gemini_api_key: formData.get('gemini_api_key') || undefined,
      gemini_model: formData.get('gemini_model'),
      openai_api_key: formData.get('openai_api_key') || undefined,
      openai_model: formData.get('openai_model'),
      temperature: parseFloat(formData.get('temperature')),
      system_language: formData.get('system_language')
    };

    try {
      state.settings = await api.updateSettings(data);
      voice.setLanguage(state.settings.system_language);
      updateHeaderBadges();
      showToast('Settings saved successfully!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };
}

function renderSettings() {
  if (!state.settings) return;
  const s = state.settings;
  const form = document.getElementById('settings-form');
  if (!form) return;

  form.elements['default_provider'].value = s.default_provider || 'gemini';
  form.elements['gemini_model'].value = s.gemini_model || 'gemini-2.5-flash';
  form.elements['openai_model'].value = s.openai_model || 'gpt-4o-mini';
  form.elements['temperature'].value = s.temperature || 0.7;
  form.elements['system_language'].value = s.system_language || 'en';

  document.getElementById('temp-value-display').textContent = s.temperature || 0.7;
  document.getElementById('gemini-status-text').textContent = s.gemini_api_key_configured ? '✅ Configured in SQLite' : '⚠️ Not yet set';
  document.getElementById('openai-status-text').textContent = s.openai_api_key_configured ? '✅ Configured in SQLite' : '⚠️ Not yet set';
}

// --- Utilities ---
function getPriorityBadgeClass(priority) {
  switch (priority) {
    case 'urgent': return 'bg-rose-900/60 text-rose-300 border border-rose-500/40';
    case 'high': return 'bg-amber-900/60 text-amber-300 border border-amber-500/40';
    case 'medium': return 'bg-indigo-900/60 text-indigo-300 border border-indigo-500/40';
    default: return 'bg-slate-700/60 text-slate-300 border border-slate-600/40';
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);
  // Code blocks
  html = html.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="bg-slate-800 px-1 py-0.5 rounded text-indigo-300">$1</code>');
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3 class="text-base font-bold text-indigo-400 mt-2 mb-1">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 class="text-lg font-bold text-white mt-3 mb-1">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 class="text-xl font-bold text-white mt-4 mb-2">$1</h1>');
  return html;
}

