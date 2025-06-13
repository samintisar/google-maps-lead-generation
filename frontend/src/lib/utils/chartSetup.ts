import {
	Chart,
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	BarElement,
	Title,
	Tooltip,
	Legend,
	ArcElement,
	Filler,
	DoughnutController,
	PieController,
	LineController,
	BarController
} from 'chart.js';

// Register all Chart.js components globally
Chart.register(
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	BarElement,
	Title,
	Tooltip,
	Legend,
	ArcElement,
	Filler,
	DoughnutController,
	PieController,
	LineController,
	BarController
);

// Chart data formatting utilities
export const formatters = {
	formatNumber: (value: number): string => {
		if (value >= 1000000) {
			return (value / 1000000).toFixed(1) + 'M';
		} else if (value >= 1000) {
			return (value / 1000).toFixed(1) + 'K';
		}
		return value.toString();
	},

	formatCurrency: (value: number): string => {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(value);
	}
};

// Export the configured Chart class
export { Chart };
export default Chart; 