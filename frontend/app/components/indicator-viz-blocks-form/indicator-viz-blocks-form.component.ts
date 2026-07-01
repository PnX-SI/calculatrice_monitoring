import { Component, OnInit } from '@angular/core';
import { AbstractControl, FormArray, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpResponse } from '@librairies/@angular/common/http';
import { IndicatorDetails } from '../../interfaces';
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

  addVizBlockForm() {
    this.vizBlocks.push(VizBlockFormComponent.buildForm(null, () => this.variables));
    this.indicatorDetails.visualizationBlockConfigs.push(null);
  }

  removeVizBlock(index: number) {
    this.vizBlocks.removeAt(index);
    this.indicatorDetails.visualizationBlockConfigs.splice(index, 1);
  }

  initVizBlocksForm() {
    this.indicatorDetails.visualizationBlockConfigs.forEach((config) => {
      this.vizBlocks.push(VizBlockFormComponent.buildForm(config, () => this.variables));
    });
    if (this.indicatorDetails.visualizationBlockConfigs.length === 0) this.addVizBlockForm();
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
    this._route.params.subscribe((params) => {
      this._data.getIndicatorDetails(params.indicatorId).subscribe((data: IndicatorDetails) => {
        this.indicatorDetails = data;
        this.initVizBlocksForm();
      });
    });
    this._route.params.subscribe((params) => {
      this._data.getIndicatorCodeVariables(params.indicatorId).subscribe((data: string[]) => {
        this.variables = data;
        this.revalidateForm();
      });
    });
  }

  onSubmit() {
    if (this.form.valid) {
      this._data
        .updateIndicatorVizBlocks(this.indicatorDetails.id, this.form.value.vizBlocks)
        .subscribe((data: HttpResponse<String>) => {
          this._router.navigate(['/calculatrice/indicator', this.indicatorDetails.id, 'details']);
        });
    }
  }
}
