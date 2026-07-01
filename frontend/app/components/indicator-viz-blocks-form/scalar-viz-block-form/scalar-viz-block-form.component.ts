import { Component, Input } from '@angular/core';
import { AbstractControl, FormControl, FormGroup, ValidationErrors } from '@angular/forms';
import { VisualizationBlockConfigParam } from '../../../interfaces';

@Component({
  selector: 'pnx-calc-scalar-viz-block-form',
  templateUrl: './scalar-viz-block-form.component.html',
  styleUrls: ['./scalar-viz-block-form.component.css'],
})
export class ScalarVizBlockFormComponent {
  @Input() public form: FormGroup;
  @Input() public variables: string[];
  @Input() public params?: VisualizationBlockConfigParam[];

  /**
   * Construit le groupe de contrôles des paramètres du bloc.
   * Appelé par le composant parent avant que le formulaire ne soit affiché, pour
   * que la validité du formulaire ne change pas pendant la détection de changements.
   * `getVariables` est évalué à chaque validation car la liste des variables est
   * chargée de façon asynchrone et peut ne pas être disponible ici.
   */
  static buildForm(
    params: VisualizationBlockConfigParam[] | undefined,
    getVariables: () => string[]
  ): FormGroup {
    return new FormGroup({
      variable: new FormControl(this.getParamValue(params, 'variable') || '', {
        nonNullable: true,
        validators: (control) => this.validateVariable(control, getVariables()),
      }),
    });
  }

  private static getParamValue(params: VisualizationBlockConfigParam[] | undefined, paramName) {
    return params?.find((elmt) => elmt.name === paramName)?.value;
  }

  private static isVariableValid(value, variables: string[] | undefined) {
    return variables?.find((elmt) => elmt === value) !== undefined;
  }

  private static validateVariable(
    control: AbstractControl,
    variables: string[] | undefined
  ): ValidationErrors | null {
    return this.isVariableValid(control.value, variables)
      ? null
      : { unknownVariable: control.value };
  }

  get variableControl() {
    return this.form.get('variable');
  }

  variableValueIsValid(value) {
    return ScalarVizBlockFormComponent.isVariableValid(value, this.variables);
  }

  get variableOptions() {
    if (this.variables === undefined) {
      return undefined;
    }
    let variableOpts = this.variables.slice();
    let variableStoredValue = ScalarVizBlockFormComponent.getParamValue(this.params, 'variable');
    if (variableStoredValue !== undefined && !this.variableValueIsValid(variableStoredValue)) {
      variableOpts.push(variableStoredValue);
    }
    return variableOpts;
  }
}
