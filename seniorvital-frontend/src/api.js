const API_BASE_URL = import.meta.env?.VITE_API_URL || 'https://seniorvital-backend.onrender.com';

// Cache en memoria para respuestas ultra-rápidas (0ms de transición entre pestañas)
const memoryCache = new Map();

// Helper to get headers
function getHeaders(contentType = 'application/json') {
  const headers = {};
  if (contentType) {
    headers['Content-Type'] = contentType;
  }
  const token = localStorage.getItem('sv_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// Fetch resiliente con timeout y cache inteligente
async function fastFetch(url, options = {}, timeoutMs = 3000, cacheKey = null) {
  // 1. Si existe en caché, lo retornamos al instante
  if (cacheKey && memoryCache.has(cacheKey)) {
    const cached = memoryCache.get(cacheKey);
    // Disparamos actualización en segundo plano (Stale-While-Revalidate)
    fetchBackground(url, options, timeoutMs, cacheKey);
    return cached;
  }

  // 2. Si no está en caché, hacemos la petición con timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Error HTTP ${response.status}`);
    }

    const data = await response.json();
    if (cacheKey) {
      memoryCache.set(cacheKey, data);
    }
    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (cacheKey && memoryCache.has(cacheKey)) {
      return memoryCache.get(cacheKey);
    }
    throw err;
  }
}

// Actualización en segundo plano silenciosa
async function fetchBackground(url, options, timeoutMs, cacheKey) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timeoutId);
    if (res.ok) {
      const freshData = await res.json();
      memoryCache.set(cacheKey, freshData);
    }
  } catch (_) {
    // Silencioso en fondo
  }
}

// Global API Object
export const api = {
  // Authentication
  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error en el inicio de sesión');
    }
    const data = await response.json();
    localStorage.setItem('sv_token', data.access_token);
    
    // Fetch user details
    const user = await this.getMe();
    localStorage.setItem('sv_user', JSON.stringify(user));
    return user;
  },

  async register(email, password, role = 'senior', profile = null) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role, profile }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error en el registro');
    }
    return response.json();
  },

  async getMe() {
    return fastFetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2500, 'user_me');
  },

  async updateProfile(profile) {
    const response = await fetch(`${API_BASE_URL}/auth/profile`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ profile }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar perfil');
    }
    
    const userStr = localStorage.getItem('sv_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      user.profile = profile;
      localStorage.setItem('sv_user', JSON.stringify(user));
      memoryCache.set('user_me', user);
    }
    return response.json();
  },

  async linkCaregiver(caregiverEmail) {
    const response = await fetch(`${API_BASE_URL}/auth/link-caregiver`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ caregiver_email: caregiverEmail }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al vincular cuidador');
    }
    return response.json();
  },

  async listSeniors() {
    return fastFetch(`${API_BASE_URL}/auth/users?role=senior`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2500, 'seniors_list');
  },

  // Routines (Ollama AI)
  async getTodayRoutine(userId) {
    return fastFetch(`${API_BASE_URL}/routines/today?user_id=${userId}`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2500, `today_routine_${userId}`);
  },

  async generateRoutine(userId, force = false) {
    const response = await fetch(`${API_BASE_URL}/routines/generate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ user_id: userId, force }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al generar la rutina con IA');
    }
    const data = await response.json();
    memoryCache.set(`today_routine_${userId}`, data);
    return data;
  },

  // Exercise Catalog
  async listExercises() {
    try {
      return await fastFetch(`${API_BASE_URL}/api/v1/exercises/`, {
        method: 'GET',
        headers: getHeaders(),
      }, 2500, 'exercises_catalog');
    } catch (_) {
      return fastFetch(`${API_BASE_URL}/catalog/exercises`, {
        method: 'GET',
        headers: getHeaders(),
      }, 2500, 'exercises_catalog');
    }
  },

  // Tracking
  async recordExercise(userId, exerciseId, sets, reps, rpe = null, feltDifficulty = null) {
    const response = await fetch(`${API_BASE_URL}/tracking/record`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        user_id: userId,
        exercise_id: exerciseId,
        sets: parseInt(sets),
        reps: parseInt(reps),
        rpe: rpe !== null ? parseInt(rpe) : null,
        felt_difficulty: feltDifficulty,
      }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al guardar el tracking');
    }
    return response.json();
  },

  // Habits
  async saveHabits(userId, dateStr, habits) {
    const response = await fetch(`${API_BASE_URL}/tracking/habits`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        user_id: userId,
        date: dateStr,
        ...habits
      }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al guardar hábitos');
    }
    const result = await response.json();
    memoryCache.set(`habits_${userId}_${dateStr}`, { ...habits, date: dateStr });
    return result;
  },

  async getHabitsForDate(userId, dateStr) {
    return fastFetch(`${API_BASE_URL}/tracking/habits/${userId}/${dateStr}`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2000, `habits_${userId}_${dateStr}`);
  },

  async getHabitsHistory(userId) {
    return fastFetch(`${API_BASE_URL}/tracking/habits/${userId}`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2500, `habits_history_${userId}`);
  },

  // Dashboard & Analytics
  async getWeeklyProgress(userId) {
    return fastFetch(`${API_BASE_URL}/dashboard/progress/${userId}`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2500, `progress_${userId}`);
  },

  async getProjection(userId) {
    return fastFetch(`${API_BASE_URL}/dashboard/projection/${userId}`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2500, `projection_${userId}`);
  },

  async getInsights(userId) {
    return fastFetch(`${API_BASE_URL}/dashboard/insights/${userId}`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2500, `insights_${userId}`);
  },

  async getResidents() {
    return fastFetch(`${API_BASE_URL}/dashboard/residents`, {
      method: 'GET',
      headers: getHeaders(),
    }, 2500, 'residents_list');
  },

  // Helper for demo logins
  getCurrentUser() {
    const userStr = localStorage.getItem('sv_user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (e) {
        return null;
      }
    }
    return null;
  },

  logout() {
    localStorage.removeItem('sv_token');
    localStorage.removeItem('sv_user');
    memoryCache.clear();
  },

  async triggerLiveAnalysis(userId) {
    const response = await fetch(`${API_BASE_URL}/dashboard/analyze/${userId}`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al ejecutar análisis clínico');
    }
    return response.json();
  },

  async sendPushNotification(userId, title, body) {
    const response = await fetch(`${API_BASE_URL}/notify/send`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ user_id: userId, title, body }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al enviar notificación push');
    }
    return response.json();
  }
};

export default api;
