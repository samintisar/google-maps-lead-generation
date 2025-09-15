import type { SavedLead, CSVExportData } from '$lib/types';

export function convertLeadsToCSV(leads: SavedLead[]): string {
	if (leads.length === 0) return '';

	const csvData: CSVExportData[] = leads.map(lead => ({
		Name: lead.displayName || '',
		Address: lead.formattedAddress || '',
		Phone: lead.internationalPhoneNumber || '', // Only international phone in Places API (New)
		Website: lead.websiteUri || '',
		Rating: lead.rating ? lead.rating.toString() : '',
		Reviews: lead.userRatingCount ? lead.userRatingCount.toString() : '',
		Category: lead.primaryType || '', // Use primaryType directly in Places API (New)
		'Business Status': lead.businessStatus || '',
		'Editorial Summary': '' // Not available in Places API (New)
	}));

	const headers = Object.keys(csvData[0]);
	const csvRows = [
		headers.join(','),
		...csvData.map(row =>
			headers.map(header => {
				const value = row[header as keyof CSVExportData];
				// Escape quotes and wrap in quotes if contains comma, quote, or newline
				if (value.includes(',') || value.includes('"') || value.includes('\n')) {
					return `"${value.replace(/"/g, '""')}"`;
				}
				return value;
			}).join(',')
		)
	];

	return csvRows.join('\n');
}

export function downloadCSV(csvContent: string, filename: string = 'leads.csv') {
	const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
	const link = document.createElement('a');

	if (link.download !== undefined) {
		const url = URL.createObjectURL(blob);
		link.setAttribute('href', url);
		link.setAttribute('download', filename);
		link.style.visibility = 'hidden';
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	}
}