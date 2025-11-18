import { appointmentsAPI } from '../appointments';
import { apiClient } from '../client';

// Mock the API client
jest.mock('../client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
  apiCall: jest.fn((promise) => promise.then(
    (response) => [response.data, null],
    (error) => [null, { message: error.message, code: error.code }]
  )),
}));

describe('Appointments API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getAll', () => {
    it('should fetch all appointments successfully', async () => {
      const mockAppointments = {
        data: [
          { id: '1', patient_id: 'p1', scheduled_at: '2024-11-20T10:00:00Z', status: 'confirmed' },
          { id: '2', patient_id: 'p2', scheduled_at: '2024-11-21T14:00:00Z', status: 'pending' },
        ],
        total: 2,
        page: 1,
        limit: 10,
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAppointments });

      const [data, error] = await appointmentsAPI.getAll();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/prm/appointments', { params: {} });
      expect(data).toEqual(mockAppointments);
      expect(error).toBeNull();
    });

    it('should handle errors when fetching appointments', async () => {
      const mockError = new Error('Network error');
      (apiClient.get as jest.Mock).mockRejectedValue(mockError);

      const [data, error] = await appointmentsAPI.getAll();

      expect(data).toBeNull();
      expect(error).toBeTruthy();
    });

    it('should pass query parameters correctly', async () => {
      (apiClient.get as jest.Mock).mockResolvedValue({ data: { data: [], total: 0 } });

      await appointmentsAPI.getAll({
        page: 2,
        limit: 20,
        status: 'confirmed',
      });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/prm/appointments', {
        params: { page: 2, limit: 20, status: 'confirmed' },
      });
    });
  });

  describe('getById', () => {
    it('should fetch a single appointment by ID', async () => {
      const mockAppointment = {
        id: '1',
        patient_id: 'p1',
        scheduled_at: '2024-11-20T10:00:00Z',
        status: 'confirmed',
      };

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockAppointment });

      const [data, error] = await appointmentsAPI.getById('1');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/prm/appointments/1');
      expect(data).toEqual(mockAppointment);
      expect(error).toBeNull();
    });

    it('should handle not found error', async () => {
      const mockError = { response: { status: 404, data: { message: 'Not found' } } };
      (apiClient.get as jest.Mock).mockRejectedValue(mockError);

      const [data, error] = await appointmentsAPI.getById('nonexistent');

      expect(data).toBeNull();
      expect(error).toBeTruthy();
    });
  });

  describe('book', () => {
    it('should book a new appointment successfully', async () => {
      const newAppointment = {
        patient_id: 'p1',
        scheduled_at: '2024-11-20T10:00:00Z',
        appointment_type: 'consultation',
      };

      const mockResponse = {
        id: '123',
        ...newAppointment,
        status: 'pending',
      };

      (apiClient.post as jest.Mock).mockResolvedValue({ data: mockResponse });

      const [data, error] = await appointmentsAPI.book(newAppointment);

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/prm/appointments', newAppointment);
      expect(data).toEqual(mockResponse);
      expect(error).toBeNull();
    });

    it('should handle validation errors', async () => {
      const invalidAppointment = {
        patient_id: '',
        scheduled_at: 'invalid-date',
      };

      const mockError = {
        response: {
          status: 400,
          data: { message: 'Validation error', details: ['Invalid date'] },
        },
      };

      (apiClient.post as jest.Mock).mockRejectedValue(mockError);

      const [data, error] = await appointmentsAPI.book(invalidAppointment as any);

      expect(data).toBeNull();
      expect(error).toBeTruthy();
    });
  });

  describe('cancel', () => {
    it('should cancel an appointment successfully', async () => {
      const mockResponse = {
        id: '1',
        status: 'cancelled',
        cancelled_at: '2024-11-19T15:00:00Z',
      };

      (apiClient.patch as jest.Mock).mockResolvedValue({ data: mockResponse });

      const [data, error] = await appointmentsAPI.cancel('1', 'Patient request');

      expect(apiClient.patch).toHaveBeenCalledWith('/api/v1/prm/appointments/1', {
        status: 'cancelled',
        cancellation_reason: 'Patient request',
      });
      expect(data).toEqual(mockResponse);
      expect(error).toBeNull();
    });
  });

  describe('reschedule', () => {
    it('should reschedule an appointment successfully', async () => {
      const newDateTime = '2024-11-21T14:00:00Z';
      const mockResponse = {
        id: '1',
        scheduled_at: newDateTime,
        status: 'confirmed',
      };

      (apiClient.patch as jest.Mock).mockResolvedValue({ data: mockResponse });

      const [data, error] = await appointmentsAPI.reschedule('1', newDateTime);

      expect(apiClient.patch).toHaveBeenCalledWith('/api/v1/prm/appointments/1', {
        scheduled_at: newDateTime,
      });
      expect(data).toEqual(mockResponse);
      expect(error).toBeNull();
    });
  });

  describe('getAvailableSlots', () => {
    it('should fetch available time slots', async () => {
      const mockSlots = [
        { start_time: '2024-11-20T09:00:00Z', end_time: '2024-11-20T09:30:00Z' },
        { start_time: '2024-11-20T10:00:00Z', end_time: '2024-11-20T10:30:00Z' },
      ];

      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockSlots });

      const [data, error] = await appointmentsAPI.getAvailableSlots(
        'prac1',
        '2024-11-20',
        '30'
      );

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/prm/appointments/available-slots',
        {
          params: {
            practitioner_id: 'prac1',
            date: '2024-11-20',
            duration: '30',
          },
        }
      );
      expect(data).toEqual(mockSlots);
      expect(error).toBeNull();
    });
  });
});
