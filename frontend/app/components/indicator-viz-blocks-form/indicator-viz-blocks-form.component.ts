import { Component, OnInit } from '@angular/core';
import { AbstractControl, FormArray, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { IndicatorDetails, VisualizationBlockConfigDetails } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { VizBlockFormComponent } from './viz-block-form/viz-block-form.component';

@Component({
  selector: 'pnx-calc-indicator-viz-blocks-form',
  templateUrl: './indicator-viz-blocks-form.component.html',
  styleUrls: ['./indicator-viz-blocks-form.component.css'],
})
export class IndicatorVizBlocksFormComponent implements OnInit {
  form: FormGroup;
  indicatorDetails: IndicatorDetails;
  variables: string[];
  scope: 'campaign' | 'overview' = 'campaign';

  constructor(
    private _route: ActivatedRoute,
    private _data: DataService,
    private _router: Router
  ) {
    this.form = new FormGroup({
      vizBlocks: new FormArray([]),
    });
  }

  get vizBlocks() {
    return this.form.controls.vizBlocks as FormArray<FormGroup>;
  }

  get blockConfigs(): VisualizationBlockConfigDetails[] {
    if (this.scope === 'overview') {
      if (!this.indicatorDetails.overviewVisualizationBlockConfigs) {
        this.indicatorDetails.overviewVisualizationBlockConfigs = [];
      }
      return this.indicatorDetails.overviewVisualizationBlockConfigs;
    }
    if (!this.indicatorDetails.visualizationBlockConfigs) {
      this.indicatorDetails.visualizationBlockConfigs = [];
    }
    return this.indicatorDetails.visualizationBlockConfigs;
  }

  addVizBlockForm() {
    this.vizBlocks.push(VizBlockFormComponent.buildForm(null, () => this.variables));
    this.blockConfigs.push(null);
  }

  removeVizBlock(index: number) {
    this.vizBlocks.removeAt(index);
    this.blockConfigs.splice(index, 1);
  }

  moveVizBlockUp(index: number) {
    if (index <= 0) {
      return;
    }
    this._swapVizBlocks(index, index - 1);
  }

  moveVizBlockDown(index: number) {
    if (index >= this.vizBlocks.length - 1) {
      return;
    }
    this._swapVizBlocks(index, index + 1);
  }

  private _swapVizBlocks(fromIndex: number, toIndex: number) {
    const control = this.vizBlocks.at(fromIndex);
    this.vizBlocks.removeAt(fromIndex);
    this.vizBlocks.insert(toIndex, control);

    const config = this.blockConfigs.splice(fromIndex, 1)[0];
    this.blockConfigs.splice(toIndex, 0, config);
  }

  get hasNoVariables(): boolean {
    return this.variables !== undefined && this.variables.length === 0;
  }

  initVizBlocksForm() {
    this.blockConfigs.forEach((config) => {
      this.vizBlocks.push(VizBlockFormComponent.buildForm(config, () => this.variables));
    });
  }

  /**
   * Les validateurs des contrôles "variable" dépendent de `variables`, chargée
   * de façon asynchrone : il faut relancer la validation quand la liste arrive.
   */
  private revalidateForm(control: AbstractControl = this.form) {
    if (control instanceof FormGroup) {
      Object.values(control.controls).forEach((child) => this.revalidateForm(child));
    } else if (control instanceof FormArray) {
      control.controls.forEach((child) => this.revalidateForm(child));
    } else {
      // TODO: check if the above is necessary => should not updateValueAndValidity check the children?
      control.updateValueAndValidity({ emitEvent: false });
    }
  }

  ngOnInit(): void {
    this.scope = this._route.snapshot.data['scope'] || 'campaign';
    this._route.params.subscribe((params) => {
      this._data.getIndicatorDetails(params.indicatorId).subscribe((data: IndicatorDetails) => {
        this.indicatorDetails = data;
        this.initVizBlocksForm();
      });
    });
    this._route.params.subscribe((params) => {
      const getVars$ =
        this.scope === 'overview'
          ? this._data.getIndicatorOverviewCodeVariables(params.indicatorId)
          : this._data.getIndicatorCodeVariables(params.indicatorId);
      getVars$.subscribe((data: string[]) => {
        this.variables = data;
        this.revalidateForm();
      });
    });
  }

  onSubmit() {
    if (this.form.valid) {
      const save$ =
        this.scope === 'overview'
          ? this._data.updateIndicatorOverviewVizBlocks(
              this.indicatorDetails.id,
              this.form.value.vizBlocks
            )
          : this._data.updateIndicatorVizBlocks(
              this.indicatorDetails.id,
              this.form.value.vizBlocks
            );
      save$.subscribe(() => {
        this._router.navigate(['/calculatrice/indicator', this.indicatorDetails.id, 'details']);
      });
    }
  }
}
