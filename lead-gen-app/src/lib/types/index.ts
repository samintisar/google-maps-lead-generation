export interface PlaceResult {
	id: string;
	displayName: string;
	formattedAddress: string;
	internationalPhoneNumber?: string;
	nationalPhoneNumber?: string;
	websiteUri?: string;
	rating?: number;
	userRatingCount?: number;
	primaryType?: string;
	primaryTypeDisplayName?: string;
	types?: string[];
	businessStatus?: string;
	editorialSummary?: string;
	location: {
		latitude: number;
		longitude: number;
	};
	priceLevel?: string;
	currentOpeningHours?: {
		openNow?: boolean;
		weekdayDescriptions?: string[];
	};
}

export interface SavedLead extends PlaceResult {
	savedAt: string;
}

export interface SearchParams {
	query: string;
	location: string;
	radius?: number;
	type?: 'textSearch' | 'nearbySearch';
}

export interface MapState {
	center: {
		lat: number;
		lng: number;
	};
	zoom: number;
	places: PlaceResult[];
	selectedPlace: PlaceResult | null;
}

export interface CSVExportData {
	Name: string;
	Address: string;
	Phone: string;
	Website: string;
	Rating: string;
	Reviews: string;
	Category: string;
	'Business Status': string;
	'Editorial Summary': string;
}

export type TabType = 'results' | 'leads';