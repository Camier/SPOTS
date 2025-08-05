/**
 * Simple Weather Service for Main Map
 * Provides weather data using Open-Meteo API
 */

export class WeatherService {
    constructor() {
        this.apiBase = 'https://api.open-meteo.com/v1';
    }

    /**
     * Get weather data for a location
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @returns {Promise<Object>} Weather data
     */
    async getWeatherData(lat, lng) {
        try {
            const url = `${this.apiBase}/forecast?` +
                `latitude=${lat}&longitude=${lng}&` +
                `current_weather=true&` +
                `daily=temperature_2m_max,temperature_2m_min,precipitation_sum&` +
                `timezone=Europe/Paris`;

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Weather API error');
            }

            return await response.json();
        } catch (error) {
            console.error('Weather fetch error:', error);
            // Return mock data on error
            return {
                current_weather: {
                    temperature: 20,
                    windspeed: 10,
                    weathercode: 0
                },
                daily: {
                    time: ['2025-08-05', '2025-08-06', '2025-08-07', '2025-08-08'],
                    temperature_2m_max: [25, 26, 24, 23],
                    temperature_2m_min: [15, 16, 14, 13],
                    precipitation_sum: [0, 2, 5, 0]
                }
            };
        }
    }
}

export default WeatherService;