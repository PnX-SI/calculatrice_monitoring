import { Component, Input } from '@angular/core';
import { ChartVisualizationBlockData } from '../../interfaces';

@Component({
  selector: 'pnx-calc-visualization-chart',
  templateUrl: './visualization-chart.component.html',
  styleUrls: ['./visualization-chart.component.css'],
})
export class VisualizationChartComponent {
  @Input() type: 'bar' | 'line' = 'bar';
  @Input() data: ChartVisualizationBlockData;
}
