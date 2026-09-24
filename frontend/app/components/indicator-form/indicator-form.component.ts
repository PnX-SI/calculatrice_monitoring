import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError } from 'rxjs/operators';
import { Indicator, IndicatorDetails, Protocol, ReferenceTable } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { UtilsService } from '../../services/utils.service';

@Component({
  selector: 'pnx-calc-indicator-form',
  templateUrl: './indicator-form.component.html',
  styleUrls: ['./indicator-form.component.css'],
})
export class IndicatorFormComponent implements OnInit {
  indicatorForm: FormGroup;
  protocols: Array<Protocol> = undefined;
  referenceTables: Array<ReferenceTable> = undefined;
  selectableReferenceTables: Array<ReferenceTable> = undefined;
  indicatorDetails: IndicatorDetails;
  mode?: 'create' | 'edit';

  constructor(
    private _data: DataService,
    private _formBuilder: FormBuilder,
    private _router: Router,
    private _utils: UtilsService,
    private _route: ActivatedRoute
  ) {
    this.indicatorForm = this._formBuilder.group({
      name: ['', { nonNullable: true }],
      description: [''],
      protocolId: ['', { nonNullable: true }],
      referenceTableIds: [[]],
    });
  }

  ngOnInit() {
    this._data.getProtocols({}).subscribe((data: Array<Protocol>) => {
      this.protocols = data;
    });
    this._data.getReferenceTables().subscribe((data: Array<ReferenceTable>) => {
      this.referenceTables = data;
      this._updateSelectableReferenceTables();
    });
    this._route.params.subscribe((params) => {
      if (params.indicatorId === undefined) {
        this.mode = 'create';
        return;
      }
      this.mode = 'edit';
      const indicatorId: number = params.indicatorId;
      this._data.getIndicatorDetails(indicatorId).subscribe((data: IndicatorDetails) => {
        this.indicatorDetails = data;
        this._updateSelectableReferenceTables();
        this.indicatorForm.setValue({
          name: data.name,
          description: data.description,
          protocolId: data.protocol.id,
          referenceTableIds: data.referenceTables.map((referenceTable) => referenceTable.id),
        });
      });
    });
  }

  /**
   * The reference tables selectable in the form are the active ones, plus any reference
   * table already attached to the indicator being edited (even if it has since been
   * deactivated) so that editing an indicator never silently drops an existing link.
   */
  private _updateSelectableReferenceTables() {
    if (!this.referenceTables) {
      return;
    }
    const linkedIds = new Set(
      (this.indicatorDetails?.referenceTables ?? []).map((referenceTable) => referenceTable.id)
    );
    this.selectableReferenceTables = this.referenceTables.filter(
      (referenceTable) => referenceTable.active || linkedIds.has(referenceTable.id)
    );
  }

  onSubmit() {
    if (this.indicatorForm.valid) {
      if (this.mode === 'create') {
        this._data
          .createIndicator(this.indicatorForm.value)
          .pipe(catchError(this._utils.handleError))
          .subscribe((data: Indicator) => {
            this._router.navigate(['/calculatrice/indicator', data.id, 'edit-code']);
          });
      } else {
        this._data
          .editIndicator(this.indicatorDetails.id, this.indicatorForm.value)
          .pipe(catchError(this._utils.handleError))
          .subscribe((data: Indicator) => {
            this._router.navigate(['/calculatrice/indicator', data.id, 'edit-code']);
          });
      }
    }
  }
}
