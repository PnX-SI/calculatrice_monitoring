import { Component, Input } from '@angular/core';
import { BarChartVisualizationBlockData } from '../../interfaces';

@Component({
  selector: 'pnx-calc-visualization-chart',
  templateUrl: './visualization-chart.component.html',
  styleUrls: ['./visualization-chart.component.css'],
})
export class VisualizationChartComponent {
  barChartType = 'bar' as const;
  @Input() data: BarChartVisualizationBlockData;
}
