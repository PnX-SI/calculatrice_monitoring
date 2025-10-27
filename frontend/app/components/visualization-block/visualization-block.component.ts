import {
  AfterViewInit,
  Component,
  ComponentRef,
  Input,
  TemplateRef,
  ViewChild,
  ViewContainerRef,
} from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { VisualizationBlockDefinition } from '../../interfaces';
import { VisualizationChartComponent } from '../visualization-chart/visualization-chart.component';
import { VisualizationScalarComponent } from '../visualization-scalar/visualization-scalar.component';

@Component({
  selector: 'pnx-calc-visualization-block',
  templateUrl: './visualization-block.component.html',
  styleUrls: ['./visualization-block.component.css'],
})
export class VisualizationBlockComponent implements AfterViewInit {
  @Input() blockDef: VisualizationBlockDefinition;
  @ViewChild('infoModal') protected modalContent: TemplateRef<any>;
  @ViewChild('viewContainer', { read: ViewContainerRef }) private _vcr: ViewContainerRef;

  constructor(private _modalService: NgbModal) {}

  ngAfterViewInit() {
    // An initialized view is needed to use the ViewContainerRef but the goal is to change the view
    // itself by adding a dynamic component. The view is already rendered so one must act
    // at the next tick with a timeout.
    setTimeout(() => {
      let ref: ComponentRef<any> = undefined;
      if (this.blockDef.type === 'scalaire') {
        ref = this._vcr.createComponent(VisualizationScalarComponent);
      } else if (this.blockDef.type === 'barChart') {
        ref = this._vcr.createComponent(VisualizationChartComponent);
      }
      ref!.setInput('data', this.blockDef.data);
    });
  }

  onInformationClick(event: MouseEvent) {
    this._modalService.open(this.modalContent, { size: 'xl' });
  }
}
