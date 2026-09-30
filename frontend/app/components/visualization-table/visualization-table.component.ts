import { Component, Input } from '@angular/core';
import { TableVisualizationBlockData } from '../../interfaces';

@Component({
  selector: 'pnx-calc-visualization-table',
  templateUrl: './visualization-table.component.html',
  styleUrls: ['./visualization-table.component.css'],
})
export class VisualizationTableComponent {
  @Input() data: TableVisualizationBlockData;
}
