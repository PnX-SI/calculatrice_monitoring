export interface Indicator {
  id: number;
  name: string;
  description: string;
  protocolId: number;
}

export interface IndicatorDetails {
  id: number;
  name: string;
  description: string;
  protocol: Protocol;
  code: string;
  visualizationBlockConfigs: VisualizationBlockConfig[];
  referenceTables: ReferenceTable[];
}

export interface Protocol {
  id: number;
  label: string;
  code: string;
}

export interface ReferenceTable {
  id: number;
  name: string;
  code: string;
}

export interface VisualizationBlockConfig {
  title: string;
  info: string;
  description: string;
  type: 'scalaire' | 'barChart';
  params: VisualizationBlockConfigParam[];
}

export interface VisualizationBlockConfigParam {
  name: string;
  value: string;
  type: 'text' | 'variable';
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
