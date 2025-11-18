import { AppointmentAgent } from '../AppointmentAgent';
import { ExecutionContext } from '../../tools/types';

// Mock OpenAI
jest.mock('openai', () => {
  return {
    default: jest.fn().mockImplementation(() => ({
      chat: {
        completions: {
          create: jest.fn().mockResolvedValue({
            choices: [
              {
                message: {
                  content: JSON.stringify({
                    intent: 'book_appointment',
                    entities: { patient_name: 'John Doe' },
                    confidence: 0.95,
                  }),
                },
              },
            ],
          }),
        },
      },
    })),
  };
});

describe('AppointmentAgent', () => {
  let agent: AppointmentAgent;
  let mockContext: ExecutionContext;

  beforeEach(() => {
    agent = new AppointmentAgent('sk-test-key');
    mockContext = {
      userId: 'user123',
      orgId: 'org123',
      sessionId: 'session123',
      requestId: 'req123',
      permissions: ['appointment.book', 'appointment.get'],
    };
  });

  describe('Initialization', () => {
    it('should initialize with correct properties', () => {
      expect(agent).toBeDefined();
      expect(agent.getCapabilities().name).toBe('AppointmentAgent');
    });

    it('should have correct tool requirements', () => {
      const capabilities = agent.getCapabilities();
      expect(capabilities.capabilities.length).toBeGreaterThan(0);
    });
  });

  describe('canHandle', () => {
    it('should return true for appointment-related intents', () => {
      expect(agent.canHandle('book an appointment')).toBe(true);
      expect(agent.canHandle('schedule appointment')).toBe(true);
      expect(agent.canHandle('cancel appointment')).toBe(true);
      expect(agent.canHandle('reschedule appointment')).toBe(true);
    });

    it('should return false for non-appointment intents', () => {
      expect(agent.canHandle('create a patient')).toBe(false);
      expect(agent.canHandle('send email')).toBe(false);
      expect(agent.canHandle('start journey')).toBe(false);
    });
  });

  describe('getCapabilities', () => {
    it('should return properly structured capabilities', () => {
      const capabilities = agent.getCapabilities();

      expect(capabilities).toHaveProperty('name');
      expect(capabilities).toHaveProperty('description');
      expect(capabilities).toHaveProperty('capabilities');
      expect(capabilities).toHaveProperty('version');

      expect(Array.isArray(capabilities.capabilities)).toBe(true);
      expect(capabilities.capabilities.length).toBeGreaterThan(0);
    });

    it('should include examples for each capability', () => {
      const capabilities = agent.getCapabilities();

      capabilities.capabilities.forEach((cap) => {
        expect(cap).toHaveProperty('name');
        expect(cap).toHaveProperty('description');
        expect(cap).toHaveProperty('examples');
        expect(Array.isArray(cap.examples)).toBe(true);
        expect(cap.examples.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Intent Analysis', () => {
    it('should correctly identify booking intent', () => {
      const bookingPhrases = [
        'book appointment for John',
        'schedule appointment with Dr. Smith',
        'create appointment tomorrow',
      ];

      bookingPhrases.forEach((phrase) => {
        expect(agent.canHandle(phrase)).toBe(true);
      });
    });

    it('should correctly identify cancellation intent', () => {
      const cancellationPhrases = [
        'cancel appointment',
        'delete appointment',
        'remove appointment',
      ];

      cancellationPhrases.forEach((phrase) => {
        expect(agent.canHandle(phrase)).toBe(true);
      });
    });
  });
});
