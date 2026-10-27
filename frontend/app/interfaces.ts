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
  sourceCode: string;
  overviewSourceCode?: string;
  visualizationBlockConfigs: VisualizationBlockConfigDetails[];
  overviewVisualizationBlockConfigs?: VisualizationBlockConfigDetails[];
  statisticalTestsSourceCode?: string;
  statisticalTestsVisualizationBlockConfigs?: VisualizationBlockConfigDetails[];
  referenceTables: ReferenceTable[];
}

export interface IndicatorAttributes {
  name: string;
  description: string;
  protocolId: number;
  referenceTableIds: number[];
}

export interface Protocol {
  id: number;
  label: string;
  code: string;
}

export interface ProtocolProperties {
  site: string[];
  visit: string[];
  observation: string[];
}

export interface ReferenceTable {
  id: number;
  name: string;
  description?: string;
  code: string;
  active: boolean;
}

export interface ReferenceTableAttributes {
  name: string;
  description?: string;
  code: string;
  encoding: string;
  separator: string;
}

export interface ReferenceTableEditAttributes {
  name: string;
  description?: string;
  encoding: string;
  separator: string;
}

export interface VisualizationBlockConfig {
  title: string;
  info: string;
  description: string;
  type: 'scalar' | 'bar_chart' | 'line_chart' | 'table';
}

export interface VisualizationBlockConfigDetails extends VisualizationBlockConfig {
  params: VisualizationBlockConfigParam[];
}

export interface VisualizationBlockConfigPayload extends VisualizationBlockConfig {
  params: { [key: string]: string };
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

export type ChartVisualizationBlockData = {
  labels: string[];
  datasets: any[];
};

export type BarChartVisualizationBlockData = ChartVisualizationBlockData;
export type LineChartVisualizationBlockData = ChartVisualizationBlockData;

export type TableVisualizationBlockData = {
  headers: string[];
  rows: string[][];
};

export type VisualizationBlockData =
  | ScalarVisualizationBlockData
  | ChartVisualizationBlockData
  | TableVisualizationBlockData;

export interface VisualizationBlockDefinition {
  title: string;
  info: string;
  description: string;
  type: 'scalaire' | 'barChart' | 'lineChart' | 'table';
  data: VisualizationBlockData;
}

export interface VisualizationError {
  type: 'public' | 'internal';
  message: string;
}

export interface Visualization {
  error?: VisualizationError;
  vizBlocks: VisualizationBlockDefinition[];
}

export interface Campaign {
  startDate: string;
  endDate: string;
}

export function serializeCampaigns(campaigns: Campaign[]): string {
  return (campaigns || [])
    .filter((campaign) => Boolean(campaign.startDate && campaign.endDate))
    .map((campaign) => `${campaign.startDate}_${campaign.endDate}`)
    .join(',');
}

export function parseCampaigns(serializedCampaigns: string): Campaign[] {
  if (!serializedCampaigns) return [];
  return serializedCampaigns
    .split(',')
    .map((serializedCampaign) => {
      const [startDate, endDate] = serializedCampaign.split('_');
      return { startDate, endDate };
    })
    .filter((campaign) => Boolean(campaign.startDate && campaign.endDate));
}

export interface ExecutionContextAttribute {
  name: string;
  type: string;
  description?: string;
}

export interface ExecutionContextObject {
  name: string;
  type: string;
  description?: string;
  attributes?: ExecutionContextAttribute[];
  itemType?: string;
  itemAttributes?: ExecutionContextAttribute[];
  nestedObjects?: Record<string, ExecutionContextObject>;
}

export interface ExecutionContextFunction {
  name: string;
  signature: string;
  description?: string;
  returnType?: string;
}

export interface IndicatorExecutionContext {
  objects: Record<string, ExecutionContextObject>;
  functions: ExecutionContextFunction[];
}
