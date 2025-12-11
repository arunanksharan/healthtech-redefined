import type { Config } from "tailwindcss"

const config = {
	darkMode: ["class"],
	content: [
		'./pages/**/*.{ts,tsx}',
		'./components/**/*.{ts,tsx}',
		'./app/**/*.{ts,tsx}',
		'./src/**/*.{ts,tsx}',
		'./lib/**/*.{ts,tsx}',
	],
	prefix: "",
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px'
			}
		},
		extend: {
			colors: {
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				success: {
					DEFAULT: 'hsl(var(--success))',
					foreground: 'hsl(var(--success-foreground))'
				},
				warning: {
					DEFAULT: 'hsl(var(--warning))',
					foreground: 'hsl(var(--warning-foreground))'
				},
				info: {
					DEFAULT: 'hsl(var(--info))',
					foreground: 'hsl(var(--info-foreground))'
				},
				urgent: 'hsl(var(--urgent))',
				scheduled: 'hsl(var(--scheduled))',
				completed: 'hsl(var(--completed))',
				cancelled: 'hsl(var(--cancelled))',
				pending: 'hsl(var(--pending))',
				sentiment: {
					positive: 'hsl(var(--sentiment-positive))',
					neutral: 'hsl(var(--sentiment-neutral))',
					negative: 'hsl(var(--sentiment-negative))',
					frustrated: 'hsl(var(--sentiment-frustrated))'
				},
				channel: {
					voice: 'hsl(var(--channel-voice))',
					whatsapp: 'hsl(var(--channel-whatsapp))',
					email: 'hsl(var(--channel-email))',
					sms: 'hsl(var(--channel-sms))',
					app: 'hsl(var(--channel-app))'
				},
				vital: {
					normal: 'hsl(var(--vital-normal))',
					warning: 'hsl(var(--vital-warning))',
					critical: 'hsl(var(--vital-critical))'
				},
				allergy: {
					severe: 'hsl(var(--allergy-severe))',
					moderate: 'hsl(var(--allergy-moderate))',
					mild: 'hsl(var(--allergy-mild))'
				},
				chart: {
					'1': 'hsl(var(--chart-1))',
					'2': 'hsl(var(--chart-2))',
					'3': 'hsl(var(--chart-3))',
					'4': 'hsl(var(--chart-4))',
					'5': 'hsl(var(--chart-5))'
				}
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			width: {
				sidebar: 'var(--sidebar-width)',
				'sidebar-collapsed': 'var(--sidebar-collapsed-width)',
				'context-panel': 'var(--context-panel-width)'
			},
			height: {
				topbar: 'var(--topbar-height)'
			},
			spacing: {
				sidebar: 'var(--sidebar-width)',
				'sidebar-collapsed': 'var(--sidebar-collapsed-width)',
				topbar: 'var(--topbar-height)',
				'context-panel': 'var(--context-panel-width)'
			},
			keyframes: {
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				},
				'collapsible-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-collapsible-content-height)'
					}
				},
				'collapsible-up': {
					from: {
						height: 'var(--radix-collapsible-content-height)'
					},
					to: {
						height: '0'
					}
				},
				'slide-in-from-right': {
					from: {
						transform: 'translateX(100%)'
					},
					to: {
						transform: 'translateX(0)'
					}
				},
				'slide-out-to-right': {
					from: {
						transform: 'translateX(0)'
					},
					to: {
						transform: 'translateX(100%)'
					}
				},
				'slide-in-from-left': {
					from: {
						transform: 'translateX(-100%)'
					},
					to: {
						transform: 'translateX(0)'
					}
				},
				'slide-out-to-left': {
					from: {
						transform: 'translateX(0)'
					},
					to: {
						transform: 'translateX(-100%)'
					}
				},
				'fade-in': {
					from: {
						opacity: '0'
					},
					to: {
						opacity: '1'
					}
				},
				'fade-out': {
					from: {
						opacity: '1'
					},
					to: {
						opacity: '0'
					}
				},
				shimmer: {
					'100%': {
						transform: 'translateX(100%)'
					}
				},
				'sound-wave': {
					'0%, 100%': {
						height: '8px'
					},
					'50%': {
						height: '24px'
					}
				},
				'pulse-ring': {
					'0%': {
						transform: 'scale(1)',
						opacity: '1'
					},
					'100%': {
						transform: 'scale(1.5)',
						opacity: '0'
					}
				},
				'spin-around': {
					'0%': {
						transform: 'translateZ(0) rotate(0)'
					},
					'15%, 35%': {
						transform: 'translateZ(0) rotate(90deg)'
					},
					'65%, 85%': {
						transform: 'translateZ(0) rotate(270deg)'
					},
					'100%': {
						transform: 'translateZ(0) rotate(360deg)'
					}
				},
				slide: {
					to: {
						transform: 'translate(calc(100cqw - 100%), 0)'
					}
				},
				'border-beam': {
					'100%': {
						'offset-distance': '100%'
					}
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'collapsible-down': 'collapsible-down 0.2s ease-out',
				'collapsible-up': 'collapsible-up 0.2s ease-out',
				'slide-in-from-right': 'slide-in-from-right 0.2s ease-out',
				'slide-out-to-right': 'slide-out-to-right 0.2s ease-out',
				'slide-in-from-left': 'slide-in-from-left 0.2s ease-out',
				'slide-out-to-left': 'slide-out-to-left 0.2s ease-out',
				'fade-in': 'fade-in 0.2s ease-out',
				'fade-out': 'fade-out 0.2s ease-out',
				shimmer: 'shimmer 2s infinite',
				'spin-around': 'spin-around calc(var(--speed) * 2) infinite linear',
				slide: 'slide var(--speed) ease-in-out infinite alternate',
				'sound-wave': 'sound-wave 0.5s ease-in-out infinite',
				'pulse-ring': 'pulse-ring 1s ease-out infinite',
				'border-beam': 'border-beam calc(var(--duration)*1s) infinite linear'
			},
		}
	},
	plugins: [require("tailwindcss-animate")],
} satisfies Config

export default config
