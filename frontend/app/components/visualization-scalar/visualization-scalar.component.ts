import { Component, Input } from '@angular/core';
import { ScalarVisualizationBlockData } from '../../interfaces';

@Component({
  selector: 'pnx-calc-visualization-scalar',
  templateUrl: './visualization-scalar.component.html',
  styleUrls: ['./visualization-scalar.component.css'],
})
export class VisualizationScalarComponent {
  @Input() data: ScalarVisualizationBlockData;
}
