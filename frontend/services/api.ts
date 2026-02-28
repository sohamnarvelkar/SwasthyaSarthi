/**
 * API Service Layer for SwasthyaSarthi Frontend
 * Handles communication with the FastAPI backend
 */

// Use relative URL to leverage Next.js proxy (configured in next.config.js)
const API_BASE_URL = '';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  language?: string;
  timestamp: Date;
}

export interface ChatResponse {
  text: string;
  language: string;
  requires_confirmation?: boolean;
  pending_order?: {
    product_name: string;
    quantity: number;
    unit_price: number;
    total_price: number;
  };
  metadata: {
    mode: 'chat' | 'voice';
    language: string;
    source: string;
    intent?: string;
    agent_trace?: any[];
  };
}

export interface VoiceResponse extends ChatResponse {
  audio_url: string | null;
}

/**
 * Send a chat message to the backend
 */
export async function sendChatMessage(
  message: string,
  userId: string = 'default',
  userEmail: string = 'user@example.com',
  language?: string,
  sessionId?: string
): Promise<ChatResponse> {
  try {
    const params = new URLSearchParams({
      message,
      user_id: userId,
      user_email: userEmail,
    });

    if (language) params.append('language', language);
    if (sessionId) params.append('session_id', sessionId);

    const response = await fetch(`${API_BASE_URL}/chat?${params}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
}

/**
 * Send a voice transcript to the backend
 * Returns both text and audio response
 */
export async function sendVoiceMessage(
  transcript: string,
  userId: string = 'default',
  userEmail: string = 'user@example.com',
  language?: string,
  sessionId?: string
): Promise<VoiceResponse> {
  try {
    const params = new URLSearchParams({
      transcript,
      user_id: userId,
      user_email: userEmail,
    });

    if (language) params.append('language', language);
    if (sessionId) params.append('session_id', sessionId);

    const response = await fetch(`${API_BASE_URL}/voice?${params}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending voice message:', error);
    throw error;
  }
}

/**
 * Get audio URL for playing voice responses
 * Audio is served directly from backend to avoid proxy issues
 */
export function getAudioUrl(audioPath: string): string {
  if (audioPath.startsWith('http')) {
    return audioPath;
  }
  // For audio, use direct backend URL since the proxy may not work well with streaming
  return `http://localhost:8000${audioPath}`;
}

/**
 * Get conversation history for a user
 */
export async function getConversationHistory(
  userId: string,
  sessionId?: string,
  limit: number = 20
): Promise<{ history: ChatMessage[] }> {
  try {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });

    if (sessionId) params.append('session_id', sessionId);

    const response = await fetch(
      `${API_BASE_URL}/conversations/${userId}?${params}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching conversation history:', error);
    return { history: [] };
  }
}

/**
 * Login user and get access token
 */
export async function loginUser(
  email: string,
  password: string
): Promise<{ access_token: string; token_type: string }> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Invalid credentials');
  }

  return response.json();
}

/**
 * Register a new user
 */
export async function registerUser(
  email: string,
  password: string,
  fullName?: string
): Promise<{ message: string; user_id: number; email: string }> {
  const params = new URLSearchParams({
    email,
    password,
  });

  if (fullName) params.append('full_name', fullName);

  const response = await fetch(`${API_BASE_URL}/register?${params}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

/**
 * Get current user info
 */
export async function getCurrentUser(
  token: string
): Promise<{
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
}> {
  const response = await fetch(`${API_BASE_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get user info');
  }

  return response.json();
}

/**
 * Get all medicines from the database
 */
export interface MedicineData {
  id: number;
  name: string;
  description: string;
  package_size: string;
  price: number;
  in_stock: boolean;
  dosage?: string;
  warnings?: string;
  category?: string;
  manufacturer?: string;
}

export async function getMedicines(): Promise<MedicineData[]> {
  const response = await fetch(`${API_BASE_URL}/medicines`);
  if (!response.ok) {
    throw new Error('Failed to fetch medicines');
  }
  return response.json();
}

/**
 * Get patient's orders
 */
export interface OrderData {
  id: number;
  patient_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  status: string;
  order_date: string;
}

export async function getPatientOrders(patientId: string): Promise<OrderData[]> {
  const response = await fetch(`${API_BASE_URL}/patients/${patientId}/orders`);
  if (!response.ok) {
    throw new Error('Failed to fetch orders');
  }
  return response.json();
}

/**
 * Get all orders (for a user)
 */
export async function getAllOrders(patientId?: string): Promise<OrderData[]> {
  let url = `${API_BASE_URL}/orders`;
  if (patientId) {
    url += `?patient_id=${patientId}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch orders');
  }
  return response.json();
}

/**
 * Get refill alerts for patients
 */
export interface RefillAlertData {
  id: number;
  patient_id: string;
  product_name: string;
  quantity: number;
  days_until_refill: number;
  alert_date: string;
  status: string;
}

export async function getRefillAlerts(status?: string): Promise<{ alerts: RefillAlertData[]; count: number }> {
  let url = `${API_BASE_URL}/refill-alerts`;
  if (status) {
    url += `?status=${status}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch refill alerts');
  }
  return response.json();
}

/**
 * Check refills - get medicines that will need refilling soon
 */
export async function checkRefills(daysAhead: number = 3): Promise<{ alerts: any[]; count: number }> {
  const response = await fetch(`${API_BASE_URL}/check-refills?days_ahead=${daysAhead}`);
  if (!response.ok) {
    throw new Error('Failed to check refills');
  }
  return response.json();
}

/**
 * Get patient profile by ID
 */
export interface PatientProfileData {
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  phone: string;
  email: string;
  address: string;
  language: string;
}

export async function getPatientProfile(patientId: string): Promise<PatientProfileData | null> {
  const response = await fetch(`${API_BASE_URL}/patients/${patientId}`);
  if (!response.ok) {
    return null;
  }
  return response.json();
}

/**
 * Get all patients (for admin)
 */
export async function getAllPatients(): Promise<PatientProfileData[]> {
  const response = await fetch(`${API_BASE_URL}/patients`);
  if (!response.ok) {
    throw new Error('Failed to fetch patients');
  }
  return response.json();
}

/**
 * Analyze prescription image
 */
export interface PrescriptionAnalysisResult {
  success: boolean;
  message?: string;
  detected_medicines: Array<{
    name: string;
    confidence: number;
    dosage?: string;
  }>;
  prescription_image?: string;
  ocr_method?: string;
  ocr_confidence?: number;
  ocr_text?: string;
}

export async function analyzePrescription(
  file: File,
  language: string = 'en'
): Promise<PrescriptionAnalysisResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language);

  const response = await fetch(`${API_BASE_URL}/analyze-prescription`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to analyze prescription');
  }

  return response.json();
}

/**
 * Create a new order
 */
export interface CreateOrderResult {
  status: 'success' | 'failed';
  order_id?: number;
  product_name?: string;
  quantity?: number;
  unit_price?: number;
  total_price?: number;
  reason?: string;
  message?: string;
}

export async function createOrder(
  patientId: string,
  productName: string,
  quantity: number
): Promise<CreateOrderResult> {
  const params = new URLSearchParams({
    patient_id: patientId,
    product_name: productName,
    quantity: quantity.toString(),
  });

  const response = await fetch(`${API_BASE_URL}/create_order?${params}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to create order');
  }

  return response.json();
}
