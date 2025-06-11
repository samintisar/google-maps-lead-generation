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

// Export the configured Chart class
export { Chart };
export default Chart; 