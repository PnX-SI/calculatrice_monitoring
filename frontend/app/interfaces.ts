export interface Indicator {
  id: number;
  name: string;
  description: string;
  protocolId: number;
}

export interface Protocol {
  id: number;
  label: string;
  code: string;
}

export interface SitesGroup {
  id: number;
  name: string;
  nbSites: number;
}

export interface Site {
  id: number;
  name: string;
}

export type ScalarVisualizationBlockData = {
  figure: number;
};

export type BarChartVisualizationBlockData = {
  labels: string[];
  datasets: any[];
};

export type VisualizationBlockData = ScalarVisualizationBlockData | BarChartVisualizationBlockData;

export interface VisualizationBlockDefinition {
  title: string;
  info: string;
  description: string;
  type: 'scalaire' | 'barChart';
  data: VisualizationBlockData;
}

export interface Campaign {
  startDate: string;
  endDate: string;
}
