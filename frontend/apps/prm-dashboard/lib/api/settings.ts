import { apiClient, apiCall } from './client';

export interface UserSettings {
    account: {
        firstName: string;
        lastName: string;
        email: string;
        phone: string;
        avatarUrl: string;
    };
    notifications: {
        email: boolean;
        push: boolean;
        sms: boolean;
    };
    appearance: {
        theme: 'light' | 'dark' | 'system';
    };
}

// In-memory store for settings (resets on reload, which is fine for a stub)
let currentSettings: UserSettings = {
    account: {
        firstName: "Rahul",
        lastName: "Sharma",
        email: "rahul.sharma@hospital.com",
        phone: "+91 98765 43210",
        avatarUrl: "/avatars/01.png"
    },
    notifications: {
        email: true,
        push: true,
        sms: false
    },
    appearance: {
        theme: 'light'
    }
};

export const settingsAPI = {
    /**
     * Get user settings
     */
    async getSettings() {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 600));
        return [currentSettings, null] as const;
    },

    /**
     * Update user settings
     */
    async updateSettings(data: Partial<UserSettings>) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Merge updates
        currentSettings = {
            ...currentSettings,
            ...data,
            account: { ...currentSettings.account, ...(data.account || {}) },
            notifications: { ...currentSettings.notifications, ...(data.notifications || {}) },
            appearance: { ...currentSettings.appearance, ...(data.appearance || {}) }
        };

        return [currentSettings, null] as const;
    }
};
