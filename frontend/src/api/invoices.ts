import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface Invoice {
  id: string;
  customer_id: string;
  invoice_number: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'reminder_sent' | 'cancelled';
  items: InvoiceItem[];
  subtotal: number;
  tax: number;
  total: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateInvoiceData {
  user_id: string;  // Add user_id field
  customer_id: string;
  invoice_number: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'reminder_sent' | 'cancelled';
  items: {
    description: string;
    quantity: number;
    unit_price: number;
    total: number;
  }[];
  subtotal: number;
  tax: number;
  total: number;
  notes?: string;  // Add notes field
  recipient_email?: string;  // Add recipient_email field
  currency_code?: string;  // Add currency_code field
}

export const getInvoices = async (): Promise<Invoice[]> => {
  const response = await axios.get(`${API_URL}/invoices/`);
  return response.data;
};

export const getInvoice = async (id: string): Promise<Invoice> => {
  const response = await axios.get(`${API_URL}/invoices/${id}`);
  return response.data;
};

export const createInvoice = async (data: CreateInvoiceData): Promise<Invoice> => {
  try {
    console.log('Creating invoice with data:', data);
    const response = await axios.post(`${API_URL}/invoices/`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    console.log('Invoice creation response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error creating invoice:', error);
    if (axios.isAxiosError(error) && error.response) {
      console.error('Error response:', error.response.data);
      throw new Error(error.response.data.detail || 'Failed to create invoice');
    }
    throw error;
  }
};

export const updateInvoice = async (id: string, invoice: Partial<Invoice>): Promise<Invoice> => {
  const response = await axios.put(`${API_URL}/invoices/${id}`, invoice);
  return response.data;
};

export const deleteInvoice = async (id: string): Promise<void> => {
  await axios.delete(`${API_URL}/invoices/${id}`);
};

export const getInvoiceStats = async (): Promise<{
  total_invoices: number;
  total_revenue: number;
  status_counts: Record<Invoice['status'], number>;
}> => {
  const response = await axios.get(`${API_URL}/invoices/stats`);
  return response.data;
};